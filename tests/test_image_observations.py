import base64
import uuid
from openhands.sdk import ImageContent
from workbench.store import put
from workbench.worker import tool_observation


def test_capture_is_forwarded_only_to_known_vision_models(tmp_path):
    ident=str(uuid.uuid4())
    image=tmp_path/'fixture.png'
    encoded='iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jL1sAAAAASUVORK5CYII='
    image.write_bytes(base64.b64decode(encoded))
    put('artifacts',{'id':ident,'path':str(image),'name':'fixture.png','run':'image-fixture'})
    result={'artifact_id':ident,'exit_status':0}
    text_only=tool_observation({'vision_enabled':False},result)
    assert not any(isinstance(content,ImageContent) for content in text_only.content)
    assert 'Do not claim to have visually inspected' in text_only.text
    visual=tool_observation({'vision_enabled':True},result)
    images=[content for content in visual.content if isinstance(content,ImageContent)]
    assert len(images)==1
    assert images[0].image_urls==['data:image/png;base64,'+encoded]
