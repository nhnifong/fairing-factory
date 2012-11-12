 Fairing Factory
=================

#### A website and pipeline for make fairings of any shape for KSP.

The website will give you an area to drag point-to-point lines from either a 1m, 2m, 3m, or 5m base, and ending in a closed cap. You can cut the fairing into a couple of peices, then select a texture, and then you submit your fairing kit order.

The page that processes that form will put the fairing kit order into a json object and lpush it into a redis list.

A python script will consume these fairing kit orders, create a directory for the order, and a directory within that for each part. It will copy any pre-made parts, such as the base, into the kit directory. Then it will lpush a fairing part order for each fairing peice into redis, as well as a fairing kit tracker

A python3 script in blender will consume these part orders, create objects and node colliders with the desired shape, as well as UV coords, and save blend files in the part directories. It will also create the cfg files for each part. It will then lpush part receipts into redis.

Another python script will consume these part receipts and confirm that the part directory is present and contains all the proper files. it will then check the corresponding kit tracker for each one. It will set this part as finished in the kit tracker, and check if all the other parts in the kit are finished. If they are, it will remove the kit tracker and assemble the kit. It deletes the .blend files if requested by the user, and zips the whole kit directory up, and copies it to the download area. Then it somehow notifies the webserver to notify the user with a download link.