########################################
# Testing the wire protocol
########################################
print("****************************************")
print("***** Testing the wire protocol... *****")
print("****************************************")
from wire_protocol import pack_packet, unpack_packet

username = "user1"
operation = 1
data = "Hello, user1!"
packet = pack_packet(username, operation, data)
unpacked_username, unpacked_operation, unpacked_data = unpack_packet(packet)

assert username == unpacked_username
assert operation == unpacked_operation
assert data == unpacked_data

username = ""
operation = 2
data = "Hello, ____!"
packet = pack_packet(username, operation, data)
unpacked_username, unpacked_operation, unpacked_data = unpack_packet(packet)

assert username == unpacked_username
assert operation == unpacked_operation
assert data == unpacked_data

print("*****************************************")
print("***** Done testing wire protocol... *****")
print("*****************************************")

########################################
# Testing the wire protocol chat app
########################################

print("*************************************************")
print("***** Testing the wire protocol chat app... *****")
print("*************************************************")
from chat_service import Chat, User

chat_app = Chat()

# Test creating a user
user1 = User(None)
assert user1.get_name() is None

# Test setting a user's name
user1.set_name("user1")
assert user1.get_name() == "user1"

# Listing the accounts in the chat app
assert chat_app.list_accounts(user1) == [(None, '<server> List of accounts: []')]
assert chat_app.online_users == {}
assert chat_app.accounts == {}

# Adding an account to the chat app
assert chat_app.create_account(user1, "user1") == [(None, '<server> Account created with username "user1".')]
assert chat_app.online_users == {"user1": None}
assert chat_app.accounts == {"user1": []}

user2 = User(None)
assert chat_app.create_account(user2, "user2") == [(None, '<server> Account created with username "user2".')]
assert chat_app.online_users == {"user1": None, "user2": None}
assert chat_app.accounts == {"user1": [], "user2": []}

# Listing the accounts in the chat app
assert chat_app.list_accounts(user1) == [(None, '<server> List of accounts: [\'user1\', \'user2\']')]

# Adding an invalid account name to the chat app
assert chat_app.create_account(user1, "y|eet") == [(None, "<server> Failed to create account. Username cannot have \" \" or \"|\".")]
assert chat_app.create_account(user1, "y eet") == [(None, "<server> Failed to create account. Username cannot have \" \" or \"|\".")]
assert chat_app.create_account(user1, "") == [(None, "<server> Failed to create account. Username cannot be empty.")]
assert chat_app.online_users == {"user1": None, "user2": None}
assert chat_app.accounts == {"user1": [], "user2": []}

# Logging in to an invalid account in the chat app
assert chat_app.login_account(user1, "notanaccount") == [(None, '<server> Failed to login. Account "notanaccount" not found.')]
assert chat_app.online_users == {"user1": None, "user2": None}

# Logging in to an already online account in the chat app
assert chat_app.login_account(user1, "user1") == [(None, '<server> Failed to login. Account "user1" is already logged in. You cannot log in to the same account from multiple clients.')]
assert chat_app.online_users == {"user1": None, "user2": None}

# Logging out of an account in the chat app
assert chat_app.logout_account(user1) == [(None, '<server> Account "user1" logged out.')]
assert chat_app.online_users == {"user2": None}
assert chat_app.accounts == {"user1": [], "user2": []}

# Logging in to an account in the chat app
assert chat_app.login_account(user1, "user1") == [(None, '<server> Account "user1" logged in.')]
assert chat_app.online_users == {"user1": None, "user2": None}

# Sending a message in the chat app
assert chat_app.send_message(user1, "user2", "Hello, user2!") == [(None, '<user1> Hello, user2!'), (None, '<server> Message sent to "user2".')]

# Sending a message to an invalid account in the chat app
assert chat_app.send_message(user1, "user3", "Hello, user3!") == [(None, '<server> Failed to send. Account "user3" does not exist.')]

# Sending a message to an offline account in the chat app
user3 = User(None)
assert chat_app.create_account(user3, "user3") == [(None, '<server> Account created with username "user3".')]
assert chat_app.logout_account(user3) == [(None, '<server> Account "user3" logged out.')]
assert chat_app.send_message(user1, "user3", "Hello, user3!") == [(None, '<server> Account "user3" not online. Message queued to send')]
assert chat_app.accounts == {"user1": [], "user2": [], "user3": ['<user1> Hello, user3!']}

# Getting all queued messages in the chat app
assert chat_app.login_account(user3, "user3") == [(None, '<server> Account "user3" logged in.')]
assert chat_app.online_users == {"user1": None, "user2": None, "user3": None}
assert chat_app.accounts == {"user1": [], "user2": [], "user3": ['<user1> Hello, user3!']}
assert chat_app.deliver_undelivered(user3) == [(None, '<user1> Hello, user3!')]

# Getting all queued messages in the chat app, except no messages queued
assert chat_app.deliver_undelivered(user3) == [(None, '<server> No messages queued')]
assert chat_app.accounts == {"user1": [], "user2": [], "user3": []}

# Deleting an account in the chat app
assert chat_app.online_users == {"user1": None, "user2": None, "user3": None}
assert chat_app.accounts == {"user1": [], "user2": [], "user3": []}
assert chat_app.delete_account(user1) == [(None, '<server> Account "user1" deleted.')]
assert chat_app.online_users == {"user2": None, "user3": None}
assert chat_app.accounts == {"user2": [], "user3": []}

print("******************************************************")
print("***** Done testing the wire protocol chat app... *****")
print("******************************************************")
print("\nAll tests passed!")

