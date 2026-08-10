FROM kalilinux/kali-rolling

ENV DEBIAN_FRONTEND=noninteractive \
    DISPLAY=:1 \
    USER=root

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        kali-desktop-xfce \
        tightvncserver \
        novnc \
        websockify \
        dbus-x11 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /root/.vnc && \
    echo 'password123' | vncpasswd -f > /root/.vnc/passwd && \
    chmod 600 /root/.vnc/passwd

RUN printf '#!/bin/bash\nxrdb $HOME/.Xresources\nstartxfce4 &\n' > /root/.vnc/xstartup && \
    chmod +x /root/.vnc/xstartup

EXPOSE 5900 6080

CMD bash -c "vncserver :1 -geometry 1280x720 -depth 24 && \
             websockify --web=/usr/share/novnc 6080 localhost:5900 --heartbeat=30"
