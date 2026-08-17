from typing import Optional
import mss, numpy as np, win32gui

def find_window(title_fragment:str)->Optional[int]:
    target=title_fragment.lower().strip(); found=[]
    def cb(hwnd,_):
        if win32gui.IsWindowVisible(hwnd) and target in win32gui.GetWindowText(hwnd).lower(): found.append(hwnd)
        return True
    win32gui.EnumWindows(cb,None)
    if not found: return None
    found.sort(key=lambda h:(win32gui.GetWindowRect(h)[2]-win32gui.GetWindowRect(h)[0])*(win32gui.GetWindowRect(h)[3]-win32gui.GetWindowRect(h)[1]), reverse=True)
    return found[0]

class WindowCapture:
    def __init__(self): self.sct=mss.mss()
    def capture(self, hwnd):
        l,t,r,b=win32gui.GetWindowRect(hwnd); w=max(1,r-l); h=max(1,b-t)
        shot=self.sct.grab({'left':l,'top':t,'width':w,'height':h})
        return np.asarray(shot)[:,:,:3][:,:,::-1].copy(), (l,t,r,b)
