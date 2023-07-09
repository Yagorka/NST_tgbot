
from aiogram import types, executor, Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from aiogram import Dispatcher, types

from style_transfer_model import StyleModel

from upscale_image_model import UpscaleModel
import aiogram.utils.markdown as md

from io import BytesIO
from PIL import Image

from aiogram.dispatcher.filters import Text

import os
import gc
API_TOKEN = os.environ["TG_BOT_TOKEN"]

storage = MemoryStorage()
bot = Bot(API_TOKEN)
dp = Dispatcher(bot,
                storage=storage)

@dp.message_handler(state='*', commands='help')
async def help_handler(message: types.Message, state: FSMContext):

    await bot.send_message(
        message.chat.id,
        md.text(
            md.text('/start- запуск Бота.'),
            md.text('/help - список команд.'),
            md.text('/cancel -  начать заново.'),
            md.text('/transfer_style - перенести стиль.'),
            md.text('/upscale_image - увеличить разрешение.'),
            sep='\n'
        ),
        reply_markup=types.ReplyKeyboardRemove()
    )


async def on_startup(dp):
    print('bot start!!!')

def stylize(content_img, style_img):
    """
    Вызов модели для стилизации контент-изображения
    """
    model = StyleModel()
    output = model.style_transfer(content_img, style_img)
    del model
    gc.collect()
    return output

def upscale(img_for_upresolution):
    """
    Вызов модели для стилизации контент-изображения
    """
    model = UpscaleModel()
    output = model.upscale_image(img_for_upresolution)
    del model
    gc.collect()
    return output

def pil_to_bytes(img):
    bio = BytesIO()
    bio.name = f'1_output.jpg'
    img.save(bio, 'JPEG')
    bio.seek(0)
    return bio


class ProfileStatesGroup(StatesGroup):

    photo_content = State()
    photo_style = State()

class Imagesforupscale(StatesGroup):

    photo_content = State()

def get_kb_start() -> ReplyKeyboardMarkup:
    kb = [
        [
            types.KeyboardButton(text="/UpscaleImage"),
            types.KeyboardButton(text="/StyleTransfer")
        ],
    ]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder="Choice function..."
    )
    return keyboard

def get_kb() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton('/create'))

    return kb

def get_cancel_kb() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton('/clean'))

    return kb


@dp.message_handler(commands=['clean'], state='*')
async def cmd_cancel(message: types.Message, state: FSMContext):
    if state is None:
        return

    await state.finish()
    await message.reply('Вы удалили изображения',
                        reply_markup=get_kb_start())


@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message) -> None:
    await message.answer('Добро пожаловать! 👋\n\nUpscaleImage - улучшить качество изображения. \n\nStyleTransfer - перенсти стиль с одного изображения на другое.' ,
                         reply_markup=get_kb_start())


@dp.message_handler(commands=['StyleTransfer', 'transfer_style'])
async def cmd_create(message: types.Message) -> None:
    await message.reply("Отправьте изображение контента!",
                        reply_markup=get_cancel_kb())
    await ProfileStatesGroup.photo_content.set()  # установили состояние фото

@dp.message_handler(commands=['UpscaleImage', 'upscale_image'])
async def cmd_create(message: types.Message) -> None:
    await message.reply("Выберите изображение!",
                        reply_markup=get_cancel_kb())
    await Imagesforupscale.photo_content.set()  # установили состояние фото


@dp.message_handler(lambda message: not message.photo, state=ProfileStatesGroup.photo_content)
async def check_photo_content(message: types.Message):
    await message.reply('Это не изображение!')



@dp.message_handler(content_types=['photo'], state=ProfileStatesGroup.photo_content)
async def load_photo_content(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        data['photo_content'] = message.photo[-1].file_id

    await message.reply('Теперь отправьте  изображение стиля!')
    await ProfileStatesGroup.next()

@dp.message_handler(lambda message: not message.photo, state=Imagesforupscale.photo_content)
async def check_photo_content(message: types.Message):
    await message.reply('Это не изображение!')



@dp.message_handler(content_types=['photo'], state=Imagesforupscale.photo_content)
async def load_photo_content(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        data['photo_content'] = message.photo[-1].file_id
        file_info_content = await bot.get_file(data['photo_content'])
        content_img = await bot.download_file(file_info_content.file_path)
    im = Image.open(content_img)
    s1, s2 = im.size
    await message.answer(f'Ваше изображение размерности {s1}x{s2}')
    if max(im.size)<=2200:
        await message.reply('Размер изображения увеличивается в 4 раза! Ожидайте...')
        output_image = upscale(im)
        s1e, s2e = output_image.size 
        await message.answer(f'Ваше изображение стало размерности {s1e}x{s2e}')
        output_byte_image = pil_to_bytes(output_image)
        await bot.send_photo(chat_id=message.from_user.id, photo=output_byte_image)
        await message.answer("Готово!👍👍\n\nЕсли хочешь попробовать еще, жми👇👇", reply_markup=get_cancel_kb())
        await state.finish()
    else:
        await message.reply('Изображение слишком большое! \n\n Выберите другое с максимальным разрешением 2000 пикселей по одной стороне!', reply_markup=get_cancel_kb())
        


@dp.message_handler(lambda message: not message.photo, state=ProfileStatesGroup.photo_style)
async def check_photo_style(message: types.Message):
    await message.reply('Это не изображение!')

@dp.message_handler(content_types=['photo'], state=ProfileStatesGroup.photo_style)
async def load_photo_style(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        data['photo_style'] = message.photo[-1].file_id

        file_info_content = await bot.get_file(data['photo_content'])
        content_img = await bot.download_file(file_info_content.file_path)
        file_info_style = await bot.get_file(data['photo_style'])
        style_img = await bot.download_file(file_info_style.file_path)

        # await bot.send_photo(chat_id=message.from_user.id,
        #                      photo=data['photo_content'],
        #                      caption=f"Ваше изображение")
        # await bot.send_photo(chat_id=message.from_user.id,
        #                      photo=data['photo_style'],
        #                      caption=f"Ваше фото стиля")

    await message.reply('Выполняется перенос стиля... (≈55 сек.)')
    
    # print(type(content_img))
    output_image = stylize(content_img, style_img)
    output_byte_image = pil_to_bytes(output_image)
    await bot.send_photo(chat_id=message.from_user.id, photo=output_byte_image)
    await message.answer("Готово!👍👍\n\nЕсли хочешь попробовать еще, жми👇👇", reply_markup=get_cancel_kb())
    await state.finish()


if __name__ == '__main__':
    executor.start_polling(dp,
                           skip_updates=True)