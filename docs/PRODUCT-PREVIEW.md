# Desk Yantra product preview

Open `http://127.0.0.1:8765/?preview=1` while Desk Yantra is running. With a frontend development server, open its displayed URL with `?preview=1`. The preview does not require pairing and does not call the app API. It contains only illustrative data and performs no model, file, shell, network, or account actions.

The five clickable stages show the intended first-run experience: set up a bot with a model and bounded workspace; watch its investigation; approve or deny an exact change; inspect the result and execution evidence; and recover after an uncertain interruption. The example is a code repair in an isolated sandbox. The preview is a product-direction artifact for owner feedback, not a claim that every illustrated interaction is already implemented in the live app.

The existing live app already has named agent profiles, local and hosted provider connections, grants, exact approvals, run events, artifact downloads, review resolution and a task tree. The preview gives these capabilities a simpler chat-first shape. The final visual design, bot identity/roster, onboarding, and the wording for outcome evidence need owner and usability review before becoming the default live UI. Connected apps, proactive routines, shared bot teams, or autonomous external actions are not implied by this preview.

The local `OpenMausBot` checkout at revision `4e22b4d9b` was consulted for its bot-roster/chat-first product framing and design principles. Its README and `DESIGN.md` were read; no source, assets, text, or branding were copied. Desk Yantra retains its execution-time grant and exact-approval boundary even where another product uses a different permission model.
