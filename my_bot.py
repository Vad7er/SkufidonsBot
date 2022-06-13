from __future__ import print_function
from io import BytesIO
from PIL import Image

import logging
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram import Bot, Dispatcher, executor, types


import torchvision.transforms as transforms


from style_transfer import model_cnn,cnn_normalization_mean, cnn_normalization_std,StyleTransfer


import aiohttp
from aiogram.utils.helper import Helper, HelperMode, ListItem



API_TOKEN = '5453938607:AAHgtQ_aS5evmgv_kRp0vxv8trN7Z20SRic'

SAVING_PATH = "C:/Users/Asus/Desktop/tg_bot/"


class States(Helper):
    mode = HelperMode.snake_case

    A_WAITING_FOR_1ST_PIC = ListItem()
    B_WAITING_FOR_2ND_PIC = ListItem()
    C_WORKING = ListItem()
    D_FINAL = ListItem()


imsize = 512

loader = transforms.Compose([
    transforms.Resize((imsize, imsize)), # scale imported image
    transforms.ToTensor()])  # transform it into a torch tensor

unloader = transforms.ToPILImage()


def to_tensor(image):
    image = Image.open(SAVING_PATH + image,'r')
    image = loader(image).unsqueeze(0)
    return image




logging.basicConfig(level=logging.INFO)


bot = Bot(token=API_TOKEN)   #объявляем бота
dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(LoggingMiddleware())


st = StyleTransfer()


@dp.message_handler(commands=['start','help'])
async def send_welcome(message: types.Message):
    state = dp.current_state(user=message.from_user.id)
    await state.set_state(States.all()[0])
    await message.reply("Отправьте боту ""/style_transfer"",чтобы начать перенос стиля ")


@dp.message_handler()
async def bad_message(message: types.Message):
    await message.reply('Напишите боту "/start" или "/help" ')


@dp.message_handler(state=States.all()[0], commands=['style_transfer'])
async def starting_style_transfer(message: types.Message):
    await message.reply('Пришлите фото контента')


@dp.message_handler(state=States.all()[0], content_types=['photo'])
async def content_pic(message: types.Message):
    state = dp.current_state(user=message.from_user.id)
    await message.photo[-1].download(str(message.from_user.id) + 'content.jpg')
    await state.set_state(States.all()[1])
    await message.reply('Вы прислали фото контента,теперь пришлите фото стиля')

@dp.message_handler(state=States.all()[1], content_types=['photo'])
async def style_pic(message: types.Message):
    state = dp.current_state(user=message.from_user.id)
    await message.photo[-1].download(str(message.from_user.id) + 'style.jpg')
    await state.set_state(States.all()[2])
    await message.reply('Вы прислали фото стиля,теперь отправьте "/start_st",чтобы начать обработку.'
                        'Или Вы можете отправить "/cancel",чтобы прислать на обработку новые фото')



@dp.message_handler(state=States.A_WAITING_FOR_1ST_PIC | States.B_WAITING_FOR_2ND_PIC | States.C_WORKING,commands=['cancel'])
async def canceling(message: types.Message):
    state = dp.current_state(user=message.from_user.id)
    await state.set_state(States.all()[0])
    await message.reply('Отмена,напишите боту "/style_transfer"')


@dp.message_handler(state=States.A_WAITING_FOR_1ST_PIC | States.B_WAITING_FOR_2ND_PIC)
async def unknown_message(msg: types.Message):
    await msg.reply('Нужно прислать фото')


@dp.message_handler(state=States.all()[2], commands=['start_st'])
async def starting_working(message: types.Message):
    await bot.send_message(message.from_user.id,'Идет обработка,это может занять несколько часов.......))))))))))))')
    state = dp.current_state(user=message.from_user.id)
    bio = BytesIO()
    bio.name = 'image.jpeg'
    image = unloader((st.run_style_transfer(model_cnn, cnn_normalization_mean, cnn_normalization_std,
                            to_tensor(str(message.from_user.id) + 'content.jpg'),
                                to_tensor(str(message.from_user.id) + 'style.jpg'),
                               to_tensor(str(message.from_user.id) + 'content.jpg'),
                                num_steps = 100,
                                style_weight=3500000, content_weight=3)).squeeze(0))
    image.save(bio, 'JPEG')
    bio.seek(0)
    await bot.send_photo(message.from_user.id,photo=bio)
    await state.set_state(States.all()[3])


@dp.message_handler(state=States.all()[3])
async def transfer_done(message: types.Message):
    await message.reply('Чтобы еще раз обработать фото напишите "/again" ')


@dp.message_handler(state=States.all()[3],commands=['again'])
async def transfering_again(message: types.Message):
    state = dp.current_state(user=message.from_user.id)
    await state.set_state(States.all()[0])


import os
PORT = int(os.environ.get('PORT', 5000))


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
   # executor.start_webhook(listen="0.0.0.0",
    #                      port=int(PORT),
    #                      url_path=API_TOKEN)
   # executor.bot.setWebhook('https://secret-island-37191.herokuapp.com/' + API_TOKEN)
