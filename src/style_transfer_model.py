import torch
import torch.optim as optim
import torch.nn as nn
from torch.nn.functional import mse_loss
import torchvision.models as models
from torchvision.transforms.functional import resize, to_tensor, to_pil_image

from PIL import Image
from styleTransfer_utils import *
from io import BytesIO

class StyleModel():
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        #print("Device is", self.device)
        self.cnn = models.vgg19(pretrained=False).features.to(self.device)
        pretrained_dict = torch.load('weights/vgg_conv.pth')

        for param, item in zip(self.cnn.parameters(), pretrained_dict.keys()):
            param.data = pretrained_dict[item].type(torch.FloatTensor).to(self.device)

        self.cnn.requires_grad_(False)

        # Initialize outputs dic
        self.outputs = {}

        # Hook definition
        def save_output(name):

            # The hook signature
            def hook(module, module_in, module_out):
                self.outputs[name] = module_out
            return hook

        # Define layers
        self.style_layers = [1, 6, 11, 20, 29]
        self.content_layers = [22]

        # Define weights for layers
        self.style_weights = [1e3/n**2 for n in [64,128,256,512,512]]
        self.content_weights = [1]

        # Register hook on each layer with index on array "style_layers"
        for layer in self.style_layers:
            handle = self.cnn[layer].register_forward_hook(save_output(layer))

        # Register hook on each layer with index on array "content_layers"
        for layer in self.content_layers:
            handle = self.cnn[layer].register_forward_hook(save_output(layer))

    def get_style_model_and_losses(self, content_im, style_im):

        # Forward pass using style image for get activations of selected layers. Calculate gram Matrix for those activations
        self.cnn(style_im)
        gramm_style_targets = [gramm(self.outputs[key]) for key in self.style_layers]

        # Forward pass using content image for get activations of selected layers.
        self.cnn(content_im)
        target_content_im_activations = [self.outputs[key] for key in self.content_layers]

            # Define image to optimize as copy of content image
        opt_img = content_im.clone()
        opt_img.requires_grad_(True)

        # Set optimizer
        optimizer = optim.LBFGS([opt_img])

        n_iters = 500
        # log_every = 250
        iter_ = [0]

        while iter_[0] <= n_iters:
            # print(iter_)
            def closure():

                optimizer.zero_grad()

                # Forward pass using opt_img. Get activations of selected layers for image opt_img. Calculate gram Matrix for style activations
                self.cnn(opt_img)
                opt_img_style_im_activations = [self.outputs[key] for key in self.style_layers]
                opt_img_content_im_activations = [self.outputs[key] for key in self.content_layers]

                # Compute loss for each activation
                losses = []
                # Losses for style activations (mse loss with gram matrix)
                for activations in zip(opt_img_style_im_activations , gramm_style_targets, self.style_weights):
                    losses.append(gram_loss(*activations).unsqueeze(0))
                # Losses for content activations (mse loss)
                for activations in zip(opt_img_content_im_activations, target_content_im_activations, self.content_weights):
                    losses.append(content_loss(*activations).unsqueeze(0))

                total_loss = torch.cat(losses).sum()
                total_loss.backward()

                # Display results: print Loss value and show images
                # if iter_ % log_every == 0:
                #     printResults(style_im, content_im, opt_img, iter_, total_loss)

                iter_[0] += 1

                return total_loss

            optimizer.step(closure)
        return opt_img

    def style_transfer(self, image_content, image_style):

        img_size = 512

        # Prepare content and style data
        content_im = prep_img(image_content, img_size).to(self.device)
        style_im = prep_img(image_style, img_size).to(self.device)

        output = self.get_style_model_and_losses(content_im, style_im)
        res_img = to_pil(output.squeeze(0))
        #bio = image_to_byte_array(res_img)
        torch.cuda.empty_cache()
        return res_img

def postprocess(data):
    img = data.clone().clamp(0, 255).numpy()
    img = img.transpose(1, 2, 0).astype("uint8")
    img = Image.fromarray(img)
    bio = BytesIO()
    bio.name = f'1_output.jpeg'
    img.save(bio, 'JPEG')
    bio.seek(0)
    return bio

def image_to_byte_array(image: Image) -> bytes:
    # BytesIO is a file-like buffer stored in memory
    imgByteArr = BytesIO()
    # image.save expects a file-like as a argument
    image.save(imgByteArr, format=image.format)
    # Turn the BytesIO object back into a bytes object
    imgByteArr = imgByteArr.getvalue()
    return imgByteArr

# Computes Gram matrix for the input batch tensor.
#    Args: tnsr (torch.Tensor): input tensor of the Size([B, C, H, W]).
#    Returns:  G (torch.Tensor): output tensor of the Size([B, C, C]).
def gramm(tnsr: torch.Tensor) -> torch.Tensor:

    b,c,h,w = tnsr.size()
    F = tnsr.view(b, c, h*w)
    G = torch.bmm(F, F.transpose(1,2))
    G.div_(h*w)
    return G

# Computes MSE Loss for 2 Gram matrices
def gram_loss(input: torch.Tensor, gramm_target: torch.Tensor, weight: float = 1.0):

    loss = weight * mse_loss(gramm(input), gramm_target)
    return loss

# Computes MSE Loss for 2 tensors, with weight
def content_loss(input: torch.Tensor, target: torch.Tensor, weight: float = 1.0):

    loss = weight * mse_loss(input, target)
    return loss

if __name__ == '__main__':
    Style_transfer = StyleModel()
    image_content = '/home/yagor/Рабочий стол/tgbot/NST_tgbot/Images/MonetGarden3.jpg'
    image_style = '/home/yagor/Рабочий стол/tgbot/NST_tgbot/Styles/Gauguin.jpg'
    out = Style_transfer.style_transfer(image_content, image_style)
    byteImgIO = BytesIO()
    byteImg = byteImgIO.read(out)
    io_bytes = BytesIO(byteImg)
    # теперь открываем изображение, 
    # представленное как строка байтов
    output = Image.open(io_bytes)
    output.save('gg.png')
    # print(res)
