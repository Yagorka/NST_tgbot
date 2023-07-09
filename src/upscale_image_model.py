import torch
from PIL import Image
from RealESRGAN import RealESRGAN


class UpscaleModel():
    def __init__(self, scale=4):

        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = RealESRGAN(self.device, scale=scale)
        self.model.load_weights('weights/RealESRGAN_x4.pth', download=True)
    def upscale_image(self, image):
        # print(type(image))
        # print(image.size)
        sr_image = self.model.predict(image)
        return sr_image

if __name__ == '__main__':
    Style_transfer = UpscaleModel()
    image_content_name = '/home/yagor/Рабочий стол/tgbot/NST_tgbot/Images/MonetGarden3.jpg'
    image_content = Image.open(image_content_name)
    out = Style_transfer.upscale_image(image_content)
    # теперь открываем изображение, 
    # представленное как строка байтов
    out.save('gg.png')