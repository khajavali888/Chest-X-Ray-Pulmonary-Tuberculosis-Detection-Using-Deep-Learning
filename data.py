import sqlite3

# Connect to the database
conn = sqlite3.connect('users.db')

# Create a cursor object to execute SQL queries
cursor = conn.cursor()

# Execute a SELECT query to fetch data from the users table
cursor.execute("SELECT * FROM users")

# Fetch all rows from the result set
rows = cursor.fetchall()

# Close the connection
conn.close()

# Open an HTML file for writing
with open('users.html', 'w') as f:
    # Write the HTML header
    f.write('<!DOCTYPE html>\n<html>\n<head>\n<title>User Data</title>\n</head>\n<body>\n')

    # Write the table header
    f.write('<table border="1">\n<tr><th>User ID</th><th>Name</th><th>Email</th></tr>\n')

    # Write each row of data as a table row
    for row in rows:
        f.write('<tr>')
        for column in row:
            f.write(f'<td>{column}</td>')
        f.write('</tr>\n')

    # Close the table and body tags
    f.write('</table>\n</body>\n</html>')

print("HTML page generated successfully.")
