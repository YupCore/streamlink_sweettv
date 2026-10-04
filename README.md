### Streamlink Sweet.TV plugin
Custom plugin for streamlink implementing support for Sweet.TV (requires cookie authentication)

---

### Setup:
- Download [the plugin file](https://github.com/YupCore/streamlink_sweettv/blob/main/sweettv.py).
- Clone [streamlink](https://github.com/streamlink/streamlink) via git (or download via Code->Zip, then extract to a directory).
- Open your directory.
- Copy the plugin .py file into `src/streamlink/plugins/`(this will sideload the plugin).
- Run streamlink via `python -m streamlink_cli "your_sweettv_link" best --http-cookies-file "your_sweettv_cookies.txt"`.

### Questions

## How to get cookies?
I recommend using [this extension](https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc?hl=en), as it's very straightforward.
Download it, open sweet.tv(with your account logged on) and then open the extension, click "Export As"(not export all!) and now you have your cookies.
Place the .txt file wherever and just pass the path to it via --http-cookies-file argument.

***Do NOT share those cookies anywhere, as you might get your account hacked.***

## How do I know if this is safe?
Open the file, read the code, or send it to an LLM(like chatgpt or claude) and ask about it if you're unsure.

---

For help with streamlink itself, refer to the official [streamlink documentation](https://streamlink.github.io/cli.html).
