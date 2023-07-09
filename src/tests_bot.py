import unittest
from PIL import Image

from upscale_image_model import UpscaleModel
from style_transfer_model import StyleModel
import os 
class TestBOT(unittest.TestCase):

    def setUp(self) -> None:
        self.style_model = StyleModel()
        self.upscale_model = UpscaleModel()
        self.base_dir = os.getcwd()


    def test_work_style(self):
        image_content = f'{self.base_dir}/Images/MonetGarden3.jpg'
        image_style = f'{self.base_dir}/Styles/Gauguin.jpg'
        res = self.style_model.style_transfer(image_content, image_style)
        del self.style_model
        self.assertEqual(str(type(res)), "<class 'PIL.Image.Image'>")

    def test_work_upscale(self):
        image_content_name = f'{self.base_dir}/Images/MonetGarden3.jpg'
        image_content = Image.open(image_content_name)
        res = self.upscale_model.upscale_image(image_content)
        del self.upscale_model
        self.assertEqual(str(type(res)), "<class 'PIL.Image.Image'>")



if __name__ == "__main__":
    unittest.main()