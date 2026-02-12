from cryptography.fernet import Fernet
import cv2 as cv
import os
import numpy as np
key_str = os.environ['KEY']
key = key_str.encode()

cipher = Fernet(key)

filename =input("Enter the file name: ");
with open(os.path.join("images",filename),"rb") as f:
    encrypted_bytes = f.read()
decrypted_bytes = cipher.decrypt(encrypted_bytes)

nparr = np.frombuffer(decrypted_bytes,np.uint8)
image = cv.imdecode(nparr,cv.IMREAD_COLOR)
cv.imshow(filename,image)
if cv.waitKey(0) & 0xFF == ord('d'):
    cv.destroyAllWindows()
