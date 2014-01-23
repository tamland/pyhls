pyhls
=====

Features:

- Basic functionality for parsing ``master`` and ``media`` playlists
- Variant selection based on max bandwidth
- AES-128 decrypting with or without IV

Live streaming is currently not supported, only VOD


Examples
--------

Stream data:

.. code-block:: python
    import sys
    import hls
    
    url = "http://devimages.apple.com/iphone/samples/bipbop/bipbopall.m3u8"
    r = hls.get_stream(url)
    print(r.is_encrypted)
    print(r.segment_urls)
    
    for chunk in r.iter_content():
        pass
    


Dump to file:

.. code-block:: python
    import sys
    import hls

    def progress(p):
          sys.stdout.write("\r%d%%" % p)
          sys.stdout.flush()

    url = "http://devimages.apple.com/iphone/samples/bipbop/bipbopall.m3u8"
    hls.dump(url, "bipbopall.ts", progress)

