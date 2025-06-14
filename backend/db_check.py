import socket
import time
import os
import sys

def check_db_connection(host, port, max_attempts=30, delay=2):
    attempt = 1
    
    print(f"Waiting for database at {host}:{port}...")
    
    while attempt <= max_attempts:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result == 0:
                print("Database is ready!")
                return True
            
        except socket.error:
            pass
            
        print(f"Attempt {attempt} of {max_attempts}: Database is not ready yet...")
        attempt += 1
        time.sleep(delay)
    
    print(f"Database is not available after {max_attempts} attempts. Exiting...")
    return False

if __name__ == "__main__":
    db_host = os.getenv('DB_HOST', 'db')
    db_port = int(os.getenv('DB_PORT', '5432'))
    
    if not check_db_connection(db_host, db_port):
        sys.exit(1) 