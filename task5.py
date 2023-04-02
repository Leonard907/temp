from pwn import *


gdbscript = '''
init-pwndbg
continue
'''.format(**locals())
# Allows you to switch between local/GDB/remote from terminal
def start(argv=[], *a, **kw):
    if args.GDB:  # Set GDBscript below
        return gdb.debug([exe] + argv, gdbscript=gdbscript, *a, **kw)
    else:  # Run locally
        return process([exe] + argv, *a, **kw)

exe = "/task5/s1970716/vuln"
elf = context.binary = ELF(exe, checksec=True)
context.log_level = 'debug'


p = start()

p.sendlineafter(b"name?\n", "Hey! how is it going :)")
print('received:', p.recvline())


# got shell?
sleep(2) # helps because the task5.sh doesn't always register commands otherwise.
p.interactive()


p.close()
