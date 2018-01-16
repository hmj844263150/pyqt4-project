import os
import shutil

os.chdir('./icon')
for root,dirs, files in os.walk('.'):
    for file in files:
        if file.endswith('.qrc'):
            os.system('pyrcc4 -o %s_rc.py %s' % (file.rsplit('.',1)[0], file))
            try:
                os.remove('../%s_rc.py'%(file.rsplit('.', 1)[0]))
            except:
                pass
            shutil.move('%s_rc.py'%(file.rsplit('.', 1)[0]), '../')
            
os.chdir('../UI')
for root,dirs, files in os.walk('.'):
    for file in files:
        if file.endswith('.ui'):
            os.system('pyuic4 -o %s.py -x %s'%(file.rsplit('.',1)[0], file))
            try:
                os.remove('../%s.py'%(file.rsplit('.', 1)[0]))
            except:
                pass
            shutil.move('%s.py'%(file.rsplit('.', 1)[0]), '../')
             
print 'execute fin'