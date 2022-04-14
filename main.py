from datetime import datetime
import pycountry
import discord
import matplotlib.pyplot as plt
import requests

# Permissions int = 44032
TOKEN = ""
PREFIX = ">"

client = discord.Client()


@client.event
async def on_ready():
    print('Ready, Set, Go!')


@client.event
async def on_message(message: discord.Message):
    await client.wait_until_ready()
    channel: discord.TextChannel = message.channel
    if message.content.startswith(PREFIX + "device"):
        args = message.content.split(" ")[1:]

        if len(args) != 4:
            await channel.send("Invalid arguments: " + PREFIX + "device <location> <scale> <start_year(-start_month)> <end-year(-end_month)>\nExamples:\n>device Worldwide yearly 2010 2012\n>device Germany monthly 2020-01 2020-05")
            return

        if args[1] == "yearly":
            if int(args[2]) < 2009 or int(args[2]) > int(args[3]) or int(args[3]) > datetime.now().year:
                await channel.send("<:error:924715450036813824> Invalid years")
                return

        f = plt.figure(figsize=(18, 6))
        msg = await channel.send("<a:loading:924715074931798056> Fetching data, please hold on ...")
        await message.delete()
        data = get_data(args[0], args[1], args[2], args[3])
        if data == None:
            await msg.delete()
            await channel.send("<:error:924715450036813824> Invalid country")
            return
        data = data.text
        data = "\n".join(data.split("\n")[:-1])
        vendors, shares = [], []

        if args[2] == args[3]:
            for d in data.split("\n")[1:10]:
                vendor = d.split(",")[0]
                share = d.split(",")[1]
                vendors.append(vendor.replace('"', ""))
                shares.append(int(share.split(".")[0]))
        else:
            vendors = data.split("\n")[0].replace('"', "").split(",")[1:10]
            shares = []
            for i in range(0, len(vendors)):
                shares.append(0)
            for row in data.split("\n")[1:]:
                for index, share in enumerate(row.split(",")[1:10]):
                    shares[index] += int(share.split(".")[0])
            for i in range(0, len(vendors)):
                shares[i] /= len(data.split("\n")[1:10])
                shares[i] = round(shares[i])

        shares.reverse()
        vendors.reverse()

        ax: plt.Axes = f.add_subplot(121)
        args[0] = args[0][0].upper() + "".join(args[0][1:])
        plt.title(args[0] + ": " + args[2] + " - " + args[3])
        ax.barh(vendors, shares, color=[
                'black', 'red', 'green', 'blue', 'cyan', 'orange', 'yellow', 'purple', 'gray', 'green'])
        labels = []
        for index, _ in enumerate(ax.containers[0]):
            labels.append(str(shares[index]) + "%")

        ax.bar_label(ax.containers[0], labels)
        ax.set_xlim([0, 100])
        ax.grid(True, axis='x')

        f.savefig("out.png", bbox_inches='tight')
        await msg.delete()
        await channel.send(file=discord.File("out.png"))


def get_data(loc, scale, start_year, end_year, start_month=0, end_month=0):
    try:
        loc_hidden = "ww" if loc == "Worldwide" else pycountry.countries.search_fuzzy(loc)[
            0].alpha_2
    except:
        return None
    if scale.lower() == "yearly":
        url = f"https://gs.statcounter.com/vendor-market-share/chart.php?device=Mobile&device_hidden=mobile&statType_hidden=vendor&region_hidden={loc_hidden}&granularity=yearly&statType=Device%20Vendor&region={loc}&fromInt={start_year}&toInt={end_year}&fromYear={start_year}&toYear={end_year}&csv=1"
    else:
        url = f"https://gs.statcounter.com/vendor-market-share/chart.php?device=Mobile&device_hidden=mobile&statType_hidden=vendor&region_hidden={loc_hidden}&granularity=monthly&statType=Device%20Vendor&region={loc}&fromInt={start_year}{start_month}&toInt={end_year}{end_month}&fromMonthYear={start_year}-{start_month}&toMonthYear={end_year}-{end_month}&csv=1"
    data = requests.get(url)
    return data


client.run(TOKEN)
