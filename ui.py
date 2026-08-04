from os import path

# ShowList 渲染
def showLists(currentIndex : int, playlist : list, cache : dict):
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
            temp = playlist[currentIndex - 9 : currentIndex + 10]
            start_idx = currentIndex - 9
    
    max_digits = len(str(total))
    
    if total > 19 and start_idx > 0:
        print("...")
    
    for i, song in enumerate(temp):
        real_num = start_idx + i + 1
        is_current = (start_idx + i) == currentIndex
        
        # 从缓存读取元数据
        meta = cache.get(song, {})
        if meta:
            artist = meta.get('artist', '未知艺术家')
            title = meta.get('title', path.basename(song))
            display_name = f"{artist} - {title}"
        else:
            display_name = path.basename(song)  # fallback
        
        num_str = str(real_num).rjust(max_digits)
        if is_current:
            print(f"-> {num_str}. {display_name}")
        else:
            print(f"   {num_str}. {display_name}")
    
    if total > 19 and start_idx + 19 < total:
        print("... ( Total " + str(len(playlist)) + " Items )")
    
    print("-" * 50)

# 进度条渲染
def progressBar(info, scroll_offset, scroll_counter, max_display_len=40):
    """
    处理滚动信息，返回 (display_info, new_offset, new_counter)
    """
    if len(info) > max_display_len:
        info = max_display_len * ' ' + info
        scroll_counter += 1
        if scroll_counter % 2 == 0:
            scroll_offset = (scroll_offset + 1) % (len(info) + 1)
        
        if scroll_offset + max_display_len <= len(info):
            display_info = info[scroll_offset:scroll_offset + max_display_len]
        else:
            remaining = len(info) - scroll_offset
            display_info = info[scroll_offset:] + " " * (max_display_len - remaining)
    else:
        display_info = info.ljust(max_display_len)
        scroll_offset = 0
        scroll_counter = 0
    
    return display_info, scroll_offset, scroll_counter
