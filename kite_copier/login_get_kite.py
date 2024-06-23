from toolkit.fileutils import Fileutils
from omspy_brokers.bypass import Bypass
from omspy.brokers.zerodha import Zerodha


def get_kite(**kwargs):
    if kwargs.get("api_type") == "bypass":
        return get_bypass(**kwargs)
    else:
        return get_zerodha(**kwargs)


def get_bypass(**kwargs):
    try:
        tokpath = kwargs['tokpath']
        enctoken = None
        f = Fileutils()
        if f.is_file_not_2day(tokpath) is False:
            print(f'file modified today ... reading {enctoken}')
            with open(tokpath, 'r') as tf:
                enctoken = tf.read()
                print(f'enctoken sent to broker {enctoken}')
        print(kwargs)
        bypass = Bypass(userid=kwargs['userid'],
                        password=kwargs['password'],
                        totp=kwargs['totp'],
                        tokpath=kwargs['tokpath'],
                        enctoken=enctoken,
                        )
        if bypass.authenticate():
            if not enctoken:
                enctoken = bypass.kite.enctoken
                with open(tokpath, 'w') as tw:
                    tw.write(enctoken)
                    print("writing enctoken to file")
    except Exception as e:
        print(f"unable to create bypass object {e}")
    else:
        return bypass


def get_zerodha(**kwargs):
    try:
        print(kwargs)
        kite = Zerodha(user_id=kwargs['userid'],
                       password=kwargs['password'],
                       totp=kwargs['totp'],
                       api_key=kwargs['api_key'],
                       secret=kwargs['secret'],
                       tokpath=kwargs['tokpath']
                       )
        kite.authenticate()
        kite.enctoken = ""
    except Exception as e:
        print(f"exception while creating zerodha object {e}")
    else:
        return kite


if __name__ == "__main__":
    f = Fileutils()
    sec_dir = "../../../confid/"
    dictnry = f.get_lst_fm_yml(sec_dir + "bypass.yaml")
    dictnry["api_type"] = "bypass"
    dictnry["sec_dir"] = sec_dir
    kobj = get_kite(**dictnry)
    print(kobj)
