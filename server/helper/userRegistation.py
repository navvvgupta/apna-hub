from models.user import User
import bcrypt

def userRegistration(userInfo, client,clients,usernames):
    print("inside userRegistration")
    try:
        existing_user = User.objects(username=userInfo["username"]).first()
        if existing_user:
            client.send('Username already exists. Choose a different username.'.encode('utf-8'))
            return False

        hashed_password = bcrypt.hashpw(userInfo["password"].encode('utf-8'), bcrypt.gensalt())
        
        new_user = User(
            username=userInfo["username"],
            password=hashed_password.decode('utf-8'),  
            ip_address=userInfo["ip_address"],
            is_online=True
        )
        new_user.save()
        clients.append(client)
        usernames.append(userInfo["username"])
        client.send('Registration successful. Connected to server.'.encode('utf-8'))
        return True

    except Exception as e:
        client.send(f'Registration failed. Error: {str(e)}'.encode('utf-8'))
        return False