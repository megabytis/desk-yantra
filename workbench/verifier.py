import time
from .store import get, put, event, events, all_objects


def verify_run_outcome(run_id: str) -> dict:
    """Analyze the run's full execution history to verify whether the requested goal

    has empirical verification evidence, rather than trusting model self-report alone.
    """
    run = get("runs", run_id)
    history = events(run_id)
    all_artifacts = all_objects("artifacts")
    run_artifacts = [a for a in all_artifacts if a.get("run") == run_id]

    tool_calls = [item["data"] for item in history if item["kind"] == "tool_call"]
    tool_results = [item["data"] for item in history if item["kind"] in ("tool_result", "command_result")]
    commands = [item["data"] for item in history if item["kind"] == "command_result"]
    delegations = [item["data"] for item in history if item["kind"] in ("delegation", "delegation_finished")]

    # 1. State mutations
    mutations = []
    for call in tool_calls:
        op = call.get("op")
        if op == "write":
            mutations.append({"op": "write", "target": call.get("path")})
        elif op == "shell":
            mutations.append({"op": "shell", "command": call.get("command")})
        elif op == "delegate":
            mutations.append({"op": "delegate", "agent": call.get("agent")})

    # 2. Verifications observed
    verifications = []

    last_command = commands[-1] if commands else None
    last_command_failed = bool(last_command and last_command.get("exit_status") != 0)

    # Check if writes were followed by verification commands (e.g. tests or build)
    writes = [c for c in tool_calls if c.get("op") == "write"]
    if writes:
        write_times = [
            item["time"]
            for item in history
            if item["kind"] == "tool_call" and item["data"].get("op") == "write"
        ]
        last_write_time = max(write_times) if write_times else 0
        subsequent_commands = [
            item for item in history if item["kind"] == "command_result" and item["time"] >= last_write_time
        ]
        subsequent_success = [c for c in subsequent_commands if c["data"].get("exit_status") == 0]
        if subsequent_success:
            verifications.append({
                "kind": "post_mutation_test",
                "passed": True,
                "summary": f"Executed verification command with exit code 0 after edits: {subsequent_success[-1]['data'].get('command')}",
            })
        elif subsequent_commands:
            verifications.append({
                "kind": "post_mutation_test",
                "passed": False,
                "summary": f"Verification command failed with exit code {subsequent_commands[-1]['data'].get('exit_status')}: {subsequent_commands[-1]['data'].get('command')}",
            })

    # Artifact output verification
    if run_artifacts:
        verifications.append({
            "kind": "artifacts_generated",
            "passed": True,
            "summary": f"{len(run_artifacts)} artifact(s) captured ({', '.join(a.get('name', 'file') for a in run_artifacts[:3])})",
        })

    # Browser inspection verification
    browser_calls = [c for c in tool_calls if c.get("op") == "browser"]
    if browser_calls:
        browser_results = [r for r in tool_results if isinstance(r, dict) and "url" in r]
        if browser_results:
            verifications.append({
                "kind": "browser_navigation",
                "passed": True,
                "summary": f"Target page loaded and captured: {browser_results[-1].get('url')}",
            })

    # Delegation verification
    if delegations:
        failed_children = [d for d in delegations if d.get("status") not in (None, "completed")]
        if failed_children:
            verifications.append({
                "kind": "delegation",
                "passed": False,
                "summary": f"Delegated child task ended with status '{failed_children[-1].get('status')}'",
            })
        else:
            verifications.append({
                "kind": "delegation",
                "passed": True,
                "summary": "Delegated subtask(s) completed",
            })

    # A tool completing is evidence of execution, not proof that the user's
    # goal was met. Keep the checks in the report without upgrading the task.
    last_write_seq = max((item["seq"] for item in history if item["kind"] == "tool_call" and isinstance(item["data"], dict) and item["data"].get("op") == "write"), default=0)
    tool_errors = [item for item in history if item["kind"] == "tool_error" and (not last_write_seq or item["seq"] > last_write_seq)]
    read_only_calls = bool(tool_calls) and all(c.get("op") in ("read", "list") for c in tool_calls)
    read_observed = any(item["kind"] == "tool_result" for item in history)
    passing_post_write_check = any(v.get("kind") == "post_mutation_test" and v.get("passed") for v in verifications)

    # Determine overall verification status
    if last_command_failed:
        outcome = "unresolved_command_failure"
        reason = f"Last shell command exited with non-zero status ({last_command.get('exit_status')})."
    elif tool_errors:
        outcome = "tool_error"
        reason = "At least one tool action failed or was denied; inspect the event history."
    elif writes and not passing_post_write_check:
        outcome = "unverified_mutations"
        reason = "Files were modified or written, but no subsequent passing command or test verified the changes."
    elif any(v.get("passed") is False for v in verifications):
        outcome = "verification_failed"
        reason = "One or more verification checks failed."
    elif writes and passing_post_write_check:
        outcome = "checks_passed"
        reason = "A command passed after a file write. This checks execution, not the full requested goal."
    elif read_only_calls and read_observed:
        outcome = "verified_read_only"
        reason = "Read-only tool results were observed; the interpretation of those results is not checked."
    elif tool_calls:
        outcome = "unverified_actions"
        reason = "Tool actions were observed, but the requested result was not independently verified."
    else:
        outcome = "no_observation"
        reason = "No tool result was observed for this run."

    report = {
        "run_id": run_id,
        "requested_goal": run.get("task", ""),
        "total_actions": len(tool_calls),
        "mutations_count": len(mutations),
        "verifications_count": len(verifications),
        "verifications": verifications,
        "outcome": outcome,
        "verified": outcome == "verified_read_only",
        "reason": reason,
        "timestamp": time.time(),
    }

    event(run_id, "verification_contract", report)
    run["verification"] = report
    run["outcome"] = "verified" if report["verified"] else "needs_review"
    put("runs", run)
    return report

