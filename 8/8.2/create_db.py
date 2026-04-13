from database import init_db

if __name__ == "__main__":
    init_db()
    print("Table 'todos' created successfully (if not existed)")
