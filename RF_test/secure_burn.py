#import espsecure
import sys
#sys.path.append("./esptool")
import os
#import ecdsa as ecdsa
import hashlib
#import espsecure as espsecure
import espefuse
import esptool
import serial
import shutil
import os
import err_define

def read_efuse_val(esp, block_name):
    efuses = [ espefuse.EfuseField.from_tuple(esp, efuse) for efuse in espefuse.EFUSES ]
    efuse = espefuse._get_efuse(efuses, block_name)
    return efuse.get()

def burn_block_efuse(esp, efuse_name, new_value, do_not_confirm):
    class BurnEfuseParam(object):
        def __init__(self, efuse_name, new_value, do_not_confirm):
            self.efuse_name = efuse_name
            self.new_value = new_value
            self.do_not_confirm = do_not_confirm

    efuse_args = BurnEfuseParam(efuse_name = efuse_name, new_value = new_value, do_not_confirm = do_not_confirm)
    efuses = [ espefuse.EfuseField.from_tuple(esp, efuse) for efuse in espefuse.EFUSES ]
    espefuse.burn_efuse(esp, efuses, efuse_args)

def burn_block_key(esp, block, keyfile, force_write_always, no_protect_key, do_not_confirm):
    class burnKeyParam(object):
        def __init__(self, block, keyfile, force_write_always, no_protect_key, do_not_confirm):
            self.block = block
            self.keyfile = open(keyfile, 'rb')
            self.force_write_always = force_write_always
            self.no_protect_key = no_protect_key
            self.do_not_confirm = do_not_confirm
        def deinit(self):
            self.keyfile.close()
    param = burnKeyParam(block, keyfile, force_write_always,
                         no_protect_key,
                         do_not_confirm)
    efuses = [ espefuse.EfuseField.from_tuple(esp, efuse) for efuse in espefuse.EFUSES ]
    espefuse.burn_key(esp, efuses, param)
    param.deinit()

def burn_security_key(esp, downloader, secure_boot_key, flash_encrypt_key, aes_key, logger,
                      secure_boot_force_write = False, secure_boot_no_protect = False,
                      flash_encrypt_force_write = False, flash_encrypt_no_protect = False):
    if secure_boot_key:
        print "burn secure boot key"
        try:
            burn_block_key(esp = esp, block = "secure_boot", keyfile = secure_boot_key,
                           force_write_always = secure_boot_force_write, no_protect_key = secure_boot_no_protect, do_not_confirm = True)
        except esptool.FatalError, e:
            logger.error("burn secure boot key error: {}".format(e))
            raise err_define.BurnSecureBootKeyError(chip = downloader.chip, func = burn_security_key)
        burn_block_efuse(esp = esp, efuse_name = "ABS_DONE_0", new_value = 1, do_not_confirm = True)
    if flash_encrypt_key:
        print "burn flash encrypt key"
        #SET
        try:
            if 0x7f != read_efuse_val(esp = esp, block_name = 'FLASH_CRYPT_CNT'):
                burn_block_efuse(esp = esp, efuse_name = "FLASH_CRYPT_CNT", new_value = 0x7f, do_not_confirm = True)
            elif logger:
                logger.debug("FLASH_CRYPT_CNT already has same value")

            if 0xf != read_efuse_val(esp = esp, block_name = 'FLASH_CRYPT_CONFIG'):
                burn_block_efuse(esp = esp, efuse_name = "FLASH_CRYPT_CONFIG", new_value = 0xf, do_not_confirm = True)
            elif logger:
                logger.debug("FLASH_CRYPT_CONFIG already has same value")
            try:
                burn_block_key(esp = esp, block = 'flash_encryption', keyfile = flash_encrypt_key,
                               force_write_always = flash_encrypt_force_write, no_protect_key = flash_encrypt_no_protect, do_not_confirm = True)
            except esptool.FatalError, e:
                logger.error("burn flash encrypt key error: {}".format(e))
                raise err_define.BurnFlashEncryptKeyError(chip = downloader.chip, func = burn_security_key)

        except esptool.FatalError, e:
            print("error: {}".format(e))

def efuse_disable_functions(esp, logger, jtag_disable, dl_encrypt_disable, dl_decrypt_disable, dl_cache_disable):
    try:
        if jtag_disable:
            if 0x1 != read_efuse_val(esp = esp, block_name = 'JTAG_DISABLE'):
                burn_block_efuse(esp, efuse_name = "JTAG_DISABLE", new_value = 1, do_not_confirm = True)
            else:
                logger.info("JTAG_DISABLE already burnt")

        if dl_encrypt_disable:
            if 0x1 != read_efuse_val(esp = esp, block_name = 'DISABLE_DL_ENCRYPT'):
                burn_block_efuse(esp, efuse_name = "DISABLE_DL_ENCRYPT", new_value = 1, do_not_confirm = True)
            else:
                logger.info("DISABLE_DL_ENCRYPT already burnt")
        if dl_decrypt_disable:
            if 0x1 != read_efuse_val(esp = esp, block_name = 'DISABLE_DL_DECRYPT'):
                burn_block_efuse(esp, efuse_name = "DISABLE_DL_DECRYPT", new_value = 1, do_not_confirm = True)
            else:
                logger.info("DISABLE_DL_DECRYPT already burnt")
        if dl_cache_disable:
            if 0x1 != read_efuse_val(esp = esp, block_name = 'DISABLE_DL_CACHE'):
                burn_block_efuse(esp, efuse_name = "DISABLE_DL_CACHE", new_value = 1, do_not_confirm = True)
            else:
                logger.info("DISABLE_DL_CACHE already burnt")
    except esptool.FatalError, e:
        raise err_define.EfuseSetDisableError(chip = "", func = efuse_disable_functions)




def gen_encrypted_flash_image(output, plaintext, address, keyfile, flash_crypt_conf):
    class flashEncryptParam(object):
        def __init__(self, output, plaintext, address, keyfile, flash_crypt_conf):
            self.output = open(output, 'wb')
            self.plaintext_file = open(plaintext, 'rb')
            self.address = address
            self.keyfile = open(keyfile, 'rb')
            self.flash_crypt_conf = flash_crypt_conf
        def deinit(self):
            self.keyfile.close()
            self.plaintext_file.close()
            self.output.close()
    param = flashEncryptParam(output, plaintext, address, keyfile, flash_crypt_conf)
    espsecure.encrypt_flash_data(param)
    param.deinit()

def gen_secure_boot_digest(iv, image, keyfile, output):
    class bootDigest(object):
        def __init__(self, iv, image, keyfile, output):
            self.iv = iv
            self.image = open(image, 'rb')
            self.keyfile = open(keyfile, 'rb')
            self.output = output
        def deinit(self):
            self.image.close()
            self.keyfile.close()
    param = bootDigest(iv, image, keyfile, output)
    espsecure.digest_secure_bootloader(param)
    param.deinit()

def generate_private_key_digest(pem_path, digest_path):
    class keyParam(object):
        def __init__(self, key_file, digest_file):
            self.digest_file = open(digest_file, 'wb')
            self.keyfile = open(key_file, 'r')
        def deinit(self):
            self.digest_file.close()
            self.keyfile.close()
    key_param = keyParam(key_file = pem_path, digest_file = digest_path)
    espsecure.digest_private_key(key_param)
    key_param.deinit()

def gen_security_key(boot_key_file, flash_key_file, boot_pem, flash_pem, debug_mode = False):
    class KeyParam(object):
        def __init__(self, key_file):
            self.keyfile = key_file
    boot_pem_file  = boot_pem
    flash_pem_file = flash_pem
    if debug_mode:
        pass
    else:
        param = KeyParam(key_file = boot_pem_file)
        if os.path.exists(param.keyfile):
            os.remove(param.keyfile)
        espsecure.generate_signing_key(param)
        param = KeyParam(key_file = flash_pem_file)
        if os.path.exists(param.keyfile):
            os.remove(param.keyfile)
        espsecure.generate_signing_key(param)
    generate_private_key_digest(pem_path = boot_pem_file, digest_path = boot_key_file)
    generate_private_key_digest(pem_path = flash_pem_file, digest_path = flash_key_file)

if __name__=="__main__":
    path_str = "./secure"
    boot_key_file = "secure_boot_key.bin"
    flash_key_file = "flash_encrypt_key.bin"
    baud = 115200

    gen_security_key(boot_key_file = os.path.join(path_str, boot_key_file),
                     flash_key_file = os.path.join(path_str, flash_key_file),
                     boot_pem = os.path.join(path_str, "secure_boot_key.pem"),
                     flash_pem = os.path.join(path_str, "flash_encrypt_key.pem"),
                     debug_mode = False)




    #ser = serial.Serial("/dev/cu.SLAB_USBtoUART", baud, timeout=2)
    #gen_security_key(path_str, boot_key_file, flash_key_file, debug_pem_file="secure_boot_signing_key_default.pem")
    #gen_security_key(path_str, boot_key_file, flash_key_file, debug_pem_file=None)
    #burn_key(ser, baud, path_str, boot_key_file, flash_key_file)