from pathlib import Path
import re
p=Path('/usr/local/lib/python3.10/dist-packages/modeltranslation/utils.py')
if not p.exists():
    print('file-not-found')
else:
    s=p.read_text()
    PATH = Path('/usr/local/lib/python3.10/dist-packages/modeltranslation/utils.py')
    if not PATH.exists():
        print('file-not-found')
    else:
        s = PATH.read_text()
        start = s.find('def get_language_bidi')
        if start == -1:
            print('no-def')
        else:
            # find next top-level def after the function start
            m = re.search(r"\ndef \w+\(", s[start + 1 :])
            if m:
                end = start + 1 + m.start()
            else:
                end = len(s)

            new_func = (
                "def get_language_bidi(lang: str) -> bool:\n"
                "    \"\"\"\n"
                "    Check if a language is bi-directional.\n"
                "    \"\"\"\n"
                "    try:\n"
                "        lang_info = get_language_info(lang)\n"
                "        return lang_info[\"bidi\"]\n"
                "    except KeyError:\n"
                "        return False\n\n"
            )

            new_s = s[:start] + new_func + s[end:]
            if new_s == s:
                print('no-change')
            else:
                bak = PATH.with_suffix('.py.bak')
                bak.write_text(s)
                PATH.write_text(new_s)
                print('patched')
