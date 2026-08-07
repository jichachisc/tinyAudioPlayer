from os import path
import unicodedata


def get_char_width(char):
    """获取单个字符在终端中的显示宽度（全角=2，半角=1）"""
    width = unicodedata.east_asian_width(char)
    return 2 if width in ('F', 'W') else 1


def get_display_width(text):
    """获取字符串在终端中的显示宽度"""
    return sum(get_char_width(c) for c in text)


def showLists(currentIndex: int, playlist: list, cache: dict):
    """显示播放列表"""
    print("\n" + "-" * 50)

    total = len(playlist)
    if total <= 19:
        temp = playlist
        start_idx = 0
    else:
        if currentIndex < 9:
            temp = playlist[0:19]
            start_idx = 0
        elif currentIndex >= total - 9:
            temp = playlist[-19:]
            start_idx = total - 19
        else:
            temp = playlist[currentIndex - 9: currentIndex + 10]
            start_idx = currentIndex - 9

    max_digits = len(str(total))

    if total > 19 and start_idx > 0:
        print("...")

    for i, song in enumerate(temp):
        real_num = start_idx + i + 1
        is_current = (start_idx + i) == currentIndex

        meta = cache.get(song, {})
        if meta:
            artist = meta.get('artist', '未知艺术家')
            title = meta.get('title', path.basename(song))
            display_name = f"{artist} - {title}"
        else:
            display_name = path.basename(song)

        num_str = str(real_num).rjust(max_digits)
        if is_current:
            print(f"-> {num_str}. {display_name}")
        else:
            print(f"   {num_str}. {display_name}")

    if total > 19 and start_idx + 19 < total:
        print("... ( Total " + str(len(playlist)) + " Items )")

    print("-" * 50)


def progressBar(info, scroll_offset, scroll_counter, max_display_len=40):
    """
    滚动信息 - 从右向左滚动
    自动处理全角/半角字符宽度
    """
    info_w = get_display_width(info)

    if info_w > max_display_len:
        # 需要滚动：前后各加 max_display_len 个半角空格
        padding = ' ' * max_display_len
        padded = padding + info + padding
        padded_w = get_display_width(padded)

        # 滚动
        scroll_counter += 1
        if scroll_counter % 2 == 0:
            max_offset = padded_w - max_display_len
            scroll_offset = (scroll_offset + 1) % (max_offset + 1)

        # 根据 scroll_offset（显示宽度）找到起始字符位置
        pos = 0
        w = 0
        while pos < len(padded) and w < scroll_offset:
            w += get_char_width(padded[pos])
            pos += 1
        start = pos

        # 找到结束字符位置
        end_w = scroll_offset + max_display_len
        while pos < len(padded) and w < end_w:
            w += get_char_width(padded[pos])
            pos += 1
        end = pos

        display = padded[start:end]

        # 补齐半角空格（确保显示宽度固定）
        if get_display_width(display) < max_display_len:
            display += ' ' * (max_display_len - get_display_width(display))

    else:
        # 信息较短，不需要滚动
        display = info
        if get_display_width(display) < max_display_len:
            display += ' ' * (max_display_len - get_display_width(display))
        scroll_offset = 0
        scroll_counter = 0

    return display, scroll_offset, scroll_counter