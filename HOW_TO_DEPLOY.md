How to Deploy
=============

cd into ~/git-deploy/fairing-factory
merge develop into master
in index.html, change alt-editor.js to editor.js
in editor.js change port 8009 to 8008
in editor.js change dev-downloads to downloads
in blender-consume.py change develop.json to production.json
run all these commands in screens

    python serv.py -c config/production.json
    
    python multiplex.py -c config/production.json
    
    python shipping.py -c config/production.json
    
    /blender-2.64a-linux-glibc27-i686/blender -b fairing_production.blend -P blender_consume.py

run these once

    cp page/index.html /var/www/FairingFactory/index.html
    
    cp page/editor.js /var/www/FairingFactory/editor.js 