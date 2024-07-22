import io
import time

import requests
import numpy as np
from PIL import Image

uploadUrl = "http://nuwa.datawing.zhangyou.com"


def load_games():
    ret = requests.post(uploadUrl + '/nuwa/workshop/v3/api-open/game/options', json={})
    json = ret.json()
    games = []
    if json['status'] == 200:
        games = json['data']['list']

    return [f"{game['name']}[{game['id']}]" for game in games]


def load_users():
    ret = requests.post(uploadUrl + '/nuwa/workshop/v3/api-open/user/options', json={})
    json = ret.json()
    users = []
    if json['status'] == 200:
        users = json['data']['list']

    return [user['nickname'] for user in users]


def tensor_to_int(tensor, bits):
    # TODO: investigate benefit of rounding by adding 0.5 before clip/cast
    tensor = tensor.cpu().numpy() * (2 ** bits - 1)
    return np.clip(tensor, 0, (2 ** bits - 1))


def tensor_to_bytes(tensor):
    return tensor_to_int(tensor, 8).astype(np.uint8)


class Datawing:
    """
    A example node

    Class methods
    -------------
    INPUT_TYPES (dict): 
        Tell the main program input parameters of nodes.
    IS_CHANGED:
        optional method to control when the node is re executed.

    Attributes
    ----------
    RETURN_TYPES (`tuple`): 
        The type of each element in the output tuple.
    RETURN_NAMES (`tuple`):
        Optional: The name of each output in the output tuple.
    FUNCTION (`str`):
        The name of the entry-point method. For example, if `FUNCTION = "execute"` then it will run Example().execute()
    OUTPUT_NODE ([`bool`]):
        If this node is an output node that outputs a result/image from the graph. The SaveImage node is an example.
        The backend iterates on these output nodes and tries to execute all their parents if their parent graph is properly connected.
        Assumed to be False if not present.
    CATEGORY (`str`):
        The category the node should appear in the UI.
    execute(s) -> tuple || None:
        The entry point method. The name of this method must be the same as the value of property `FUNCTION`.
        For example, if `FUNCTION = "execute"` then this method's name must be `execute`, if `FUNCTION = "foo"` then it must be `foo`.
    """

    def __init__(self):
        self.games = []
        self.users = []

    @classmethod
    def INPUT_TYPES(s):
        """
            Return a dictionary which contains config for all input fields.
            Some types (string): "MODEL", "VAE", "CLIP", "CONDITIONING", "LATENT", "IMAGE", "INT", "STRING", "FLOAT".
            Input types "INT", "STRING" or "FLOAT" are special values for fields on the node.
            The type can be a list for selection.

            Returns: `dict`:
                - Key input_fields_group (`string`): Can be either required, hidden or optional. A node class must have property `required`
                - Value input_fields (`dict`): Contains input fields config:
                    * Key field_name (`string`): Name of a entry-point method's argument
                    * Value field_config (`tuple`):
                        + First value is a string indicate the type of field or a list for selection.
                        + Second value is a config for type "INT", "STRING" or "FLOAT".
        """
        return {
            "required": {
                "image": ("IMAGE",),
                "name": ("STRING", {
                    "multiline": False,  # True if you want the field to look like the one on the ClipTextEncode node
                    "default": ""
                }),
                "game_id": (load_games(),),
                "user_id": (load_users(),),
            },
            "optional": {
                "tags": ("STRING", {
                    "multiline": True,  # True if you want the field to look like the one on the ClipTextEncode node
                    "default": ""
                }),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    # RETURN_NAMES = ("image_output_name",)

    FUNCTION = "upload"

    # OUTPUT_NODE = False

    CATEGORY = "Datawing"

    def upload(self, image, name, game_id, user_id, tags):
        # i = 255. * image.cpu().numpy()
        # img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))
        img = Image.fromarray(tensor_to_bytes(image[0]))
        # 创建一个BytesIO对象
        img_byte_arr = io.BytesIO()
        # 将图片保存到BytesIO对象中
        img.save(img_byte_arr, format='JPEG')
        # 获取BytesIO对象的值，并重置读写位置
        img_byte_arr = img_byte_arr.getvalue()

        # 发送POST请求
        url = uploadUrl + '/nuwa/workshop/v3/api-open/ai/material/upload'

        if name == '' or name is None:
            name = 'datawing'

        current_timestamp = time.time()
        filename = f"{name}_{current_timestamp}.jpg"
        files = {'file': (filename, img_byte_arr, 'image/jpeg')}

        game_id = game_id[game_id.find('[') + 1: game_id.find(']')]
        data = {"name": name, "gameId": game_id, "nickname": user_id, "tags": tags}

        response = requests.post(url, files=files, data=data)
        print(f"[datawing]{response.json()}")
        return (image,)

    """
        The node will always be re executed if any of the inputs change but
        this method can be used to force the node to execute again even when the inputs don't change.
        You can make this node return a number or a string. This value will be compared to the one returned the last time the node was
        executed, if it is different the node will be executed again.
        This method is used in the core repo for the LoadImage node where they return the image hash as a string, if the image hash
        changes between executions the LoadImage node is executed again.
    """
    # @classmethod
    # def IS_CHANGED(s, image, string_field, int_field, float_field, print_to_screen):
    #    return ""


# Set the web directory, any .js file in that directory will be loaded by the frontend as a frontend extension
# WEB_DIRECTORY = "./somejs"


# A dictionary that contains all nodes you want to export with their names
# NOTE: names should be globally unique
NODE_CLASS_MAPPINGS = {
    "Datawing": Datawing
}

# A dictionary that contains the friendly/humanly readable titles for the nodes
NODE_DISPLAY_NAME_MAPPINGS = {
    "Datawing": "Datawing Upload"
}
