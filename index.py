import discord
from discord.ext import commands
import aiohttp
import asyncio
import os
from opencc import OpenCC
import base64
import shlex
import io
from google.cloud import vision
import openai

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)

cc = OpenCC('s2twp')

is_busy = False  # 是否正在處理請求


# 设置密钥路径（替换为你的实际路径）
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "ornate-node-326710-ba60b95e3540.json"
openai.api_key = "apikey"

def describe_image(image_path):
    client = vision.ImageAnnotatorClient()

    try:
        # 開啟圖片檔案並讀取其內容
        with open(image_path, "rb") as f:
            content = f.read()

        # 生成圖片物件並進行標籤辨識
        image = vision.Image(content=content)
        response = client.label_detection(image=image)

        if response.error.message:
            raise Exception(f"API 錯誤：{response.error.message}")

        # 提取標籤
        labels = [label.description for label in response.label_annotations]
        if labels:
            return "該圖片包含: " + ", ".join(labels)
        else:
            return "未能辨識圖片中的任何物體。"
    
    except Exception as e:
        return f"發生錯誤: {str(e)}"

async def on_cimage(img: str,mes: str) -> str:
    url = "http://localhost:2060/v1/chat/completions"
    headers = {"Content-Type": "application/json"}
    description = describe_image(img)
    data = {
    "model": "deepseek-r1-distill-llama-8b",
    "messages": [
        {"role": "user", "content": mes},
        {"role": "user", "content": f"分析以下場景: {description}"}
    ],
    "temperature": 0.7,
    "max_tokens": 1500
}
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data, headers=headers) as response:
                if response.status != 200:
                    return f"API 错误：{response.status}"
                result = await response.json()
                respon = result['choices'][0]['message']['content']
                traditional_response = cc.convert(respon)
                return traditional_response
    except Exception as e:
        return f"请求失败：{str(e)}"
async def on_math(mes: str) -> str:
    url = "http://localhost:2060/v1/chat/completions"
    headers = {"Content-Type": "application/json"}
    data = {
        "model": "deepseek-math-7b-instruct",
        "messages": [
            {"role": "user", "content": mes}
        ],
        "temperature": 0.7,
        "max_tokens": 1500
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data, headers=headers) as response:
                if response.status != 200:
                    return f"API 错误：{response.status}"
                result = await response.json()
                respon = result['choices'][0]['message']['content']
                traditional_response = cc.convert(respon)
                return traditional_response
    except Exception as e:
        return f"请求失败：{str(e)}"

async def on_chat(mes: str) -> str:
    url = "http://localhost:2060/v1/chat/completions"
    headers = {"Content-Type": "application/json"}
    data = {
        "model": "deepseek-r1-distill-qwen-7b",
        "messages": [
            {"role": "user", "content": mes}
        ],
        "temperature": 0.7,
        "max_tokens": 1500
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data, headers=headers) as response:
                if response.status != 200:
                    return f"API 错误：{response.status}"
                result = await response.json()
                respon = result['choices'][0]['message']['content']
                traditional_response = cc.convert(respon)
                results = traditional_response.replace("<think>", "").replace("</think>", "")
                return results
    except Exception as e:
        return f"请求失败：{str(e)}"
async def on_cchat(mes: str) -> str:

    result = openai.ChatCompletion.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": mes}]
    )
    try:
                respon = result['choices'][0]['message']['content']
                traditional_response = cc.convert(respon)
                results = traditional_response.replace("<think>", "").replace("</think>", "")
                return results
    except Exception as e:
        return f"请求失败：{str(e)}"

@bot.event
async def on_ready():
    print(f'目前登入身份：{bot.user}')
@bot.command()
async def CHAT(ctx, *, prompt: str):
    global is_busy
    
    if is_busy:
        await ctx.send(f"{ctx.author.mention} 機器人正在服務其他使用者，請稍後再試")
        return
    
    is_busy = True
    try:
        async with ctx.typing():
            response = await on_cchat(prompt)
            await ctx.send(f"{ctx.author.mention} {response[:1900]}")
    except Exception as e:
        await ctx.send(f"錯誤：{str(e)}")
    finally:
        is_busy = False  # 釋放狀態

@bot.command()
async def G(ctx, *, prompt: str):
    global is_busy
    
    if is_busy:
        await ctx.send(f"{ctx.author.mention} 機器人正在服務其他使用者，請稍後再試")
        return
    
    is_busy = True
    try:
        async with ctx.typing():
            response = await on_chat(prompt)
            await ctx.send(f"{ctx.author.mention} {response[:1900]}")
    except Exception as e:
        await ctx.send(f"錯誤：{str(e)}")
    finally:
        is_busy = False  # 釋放狀態
@bot.command()
async def GM(ctx, *, prompt: str):
    global is_busy
    
    if is_busy:
        await ctx.send(f"{ctx.author.mention} 機器人正在服務其他使用者，請稍後再試")
        return
    
    is_busy = True
    try:
        async with ctx.typing():
            prompts = shlex.split(prompt)
            if len(prompts) < 2:
                await ctx.send(f"{ctx.author.mention} 輸入格式錯誤，請提供 `圖片URL` 和 `訊息`")
                return
            
            response = await on_cimage(prompts[1], prompts[0])  # **這裡用 await**
            await ctx.send(f"{ctx.author.mention} {response[:1900]}")
    except Exception as e:
        await ctx.send(f"錯誤：{str(e)}")
    finally:
        is_busy = False  # 釋放狀態
@bot.command()
async def M(ctx, *, prompt: str):
    global is_busy
    
    if is_busy:
        await ctx.send(f"{ctx.author.mention} 機器人正在服務其他使用者，請稍後再試")
        return
    
    is_busy = True
    try:
        async with ctx.typing():
            response = await on_math(prompt)
            await ctx.send(f"{ctx.author.mention} {response[:1900]}")
    except Exception as e:
        await ctx.send(f"錯誤：{str(e)}")
    finally:
        is_busy = False  # 釋放狀態

bot.run('discord token')