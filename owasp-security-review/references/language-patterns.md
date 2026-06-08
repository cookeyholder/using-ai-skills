# Language-Specific OWASP Vulnerability Patterns

## Python (Django / Flask / FastAPI)

### SQL Injection
```python
# VULNERABLE — string formatting
User.objects.raw(f"SELECT * FROM users WHERE name = '{name}'")
cursor.execute("SELECT * FROM users WHERE email = '%s'" % email)
cursor.execute(f"INSERT INTO users VALUES ('{name}', '{email}')")

# SAFE — parameterized
User.objects.filter(name=name)
cursor.execute("SELECT * FROM users WHERE email = %s", [email])
```

### Command Injection
```python
# VULNERABLE
os.system(f"convert {user_file} output.jpg")
subprocess.run(user_input, shell=True)
os.popen(f"grep {pattern} /var/log/app.log")

# SAFE
subprocess.run(["convert", user_file, "output.jpg"], shell=False)
```

### SSTI (Jinja2 / Django Templates)
```python
# VULNERABLE
Template(f"Hello {user_input}").render()              # Jinja2
render_template_string(f"Hello {user_input}")         # Flask
django.template.Template(f"Hello {user_input}")       # Django

# SAFE
render_template("greeting.html", name=user_input)     # Auto-escaped
```

### Insecure Deserialization
```python
# VULNERABLE
pickle.loads(request.data)
yaml.load(request.body, Loader=yaml.Loader)           # Full loader
dill.loads(user_data)

# SAFE
json.loads(request.data)
yaml.safe_load(request.body)
```

### Path Traversal
```python
# VULNERABLE
open(f"/uploads/{request.args['file']}", "rb")
Path(f"/data/{filename}").read_text()

# SAFE
from pathlib import Path
base = Path("/uploads").resolve()
requested = (base / filename).resolve()
if not str(requested).startswith(str(base)):
    raise ValueError("Path traversal")
```

### Hardcoded Secrets
```python
# VULNERABLE
SECRET_KEY = "my-secret-123"
API_KEY = "sk-live-xxxxxxxxxxxxx"
DATABASE_URL = "postgres://user:pass@localhost/db"

# SAFE
import os
SECRET_KEY = os.environ["SECRET_KEY"]
```

---

## JavaScript / TypeScript (Node.js, Express, Next.js)

### SQL Injection
```javascript
// VULNERABLE — string concatenation
const query = `SELECT * FROM users WHERE name = '${userInput}'`;
db.query("SELECT * FROM users WHERE email = '" + email + "'");

// SAFE — parameterized
db.query("SELECT * FROM users WHERE name = ?", [userInput]);
await prisma.user.findMany({ where: { name: userInput } });
```

### NoSQL Injection (MongoDB)
```javascript
// VULNERABLE
db.collection("users").find({ username: req.body.username });
// Attacker sends: { "username": { "$ne": "" } } — returns all users
db.collection("users").find({ $where: `this.name == '${name}'` });

// SAFE
db.collection("users").find({ username: { $eq: req.body.username } });
// Or sanitize: assert(typeof req.body.username === "string")
```

### XSS
```javascript
// VULNERABLE
element.innerHTML = userInput;
document.write(userInput);
eval(userInput);
return <div dangerouslySetInnerHTML={{ __html: userInput }} />;

// SAFE
element.textContent = userInput;
import DOMPurify from "dompurify";
return <div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(userInput) }} />;
```

### Command Injection
```javascript
// VULNERABLE
exec(`ls ${userDir}`);
execSync(`convert ${userFile} output.jpg`);
spawn("sh", ["-c", userCommand]);

// SAFE
execFile("ls", [userDir], { shell: false });
spawn("convert", [userFile, "output.jpg"]);
```

### Path Traversal
```javascript
// VULNERABLE
fs.readFileSync(`/uploads/${req.query.file}`);
res.sendFile(req.query.file, { root: "/uploads" });

// SAFE
const path = require("path");
const safePath = path.join("/uploads", path.basename(req.query.file));
fs.readFileSync(safePath);
```

### SSRF
```javascript
// VULNERABLE
const response = await axios.get(req.query.url);
const result = await fetch(userProvidedUrl);

// SAFE
import { URL } from "url";
const parsed = new URL(userProvidedUrl);
if (!["https:"].includes(parsed.protocol)) throw new Error("Invalid protocol");
// Validate against hostname whitelist
```

### JWT Issues
```javascript
// VULNERABLE
jwt.verify(token, "hardcoded-secret");
jwt.decode(token);  // No verification at all!

// SAFE
jwt.verify(token, process.env.JWT_SECRET, { algorithms: ["HS256"] });
```

---

## Java / Spring Boot

### SQL Injection
```java
// VULNERABLE — concatenation
String query = "SELECT * FROM users WHERE name = '" + name + "'";
Statement stmt = conn.createStatement();
stmt.executeQuery(query);

// SAFE — PreparedStatement
String query = "SELECT * FROM users WHERE name = ?";
PreparedStatement ps = conn.prepareStatement(query);
ps.setString(1, name);
ps.executeQuery();
```

### XXE (XML External Entity)
```java
// VULNERABLE
DocumentBuilderFactory dbf = DocumentBuilderFactory.newInstance();
DocumentBuilder db = dbf.newDocumentBuilder();
Document doc = db.parse(new InputSource(new StringReader(xml)));

// SAFE
DocumentBuilderFactory dbf = DocumentBuilderFactory.newInstance();
dbf.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
dbf.setFeature("http://xml.org/sax/features/external-general-entities", false);
dbf.setXIncludeAware(false);
dbf.setExpandEntityReferences(false);
```

### Insecure Deserialization
```java
// VULNERABLE
ObjectInputStream ois = new ObjectInputStream(inputStream);
MyObject obj = (MyObject) ois.readObject();

// SAFE — use JSON serialization instead
ObjectMapper mapper = new ObjectMapper();
MyObject obj = mapper.readValue(json, MyObject.class);
```

### Command Injection
```java
// VULNERABLE
Runtime.getRuntime().exec("ping " + userInput);
new ProcessBuilder("sh", "-c", userCommand).start();

// SAFE — use array, no shell
Runtime.getRuntime().exec(new String[]{"ping", userInput});
```

---

## Go

### SQL Injection
```go
// VULNERABLE
query := fmt.Sprintf("SELECT * FROM users WHERE name = '%s'", name)
db.Query(query)

// SAFE
db.Query("SELECT * FROM users WHERE name = ?", name)
```

### Command Injection
```go
// VULNERABLE
exec.Command("sh", "-c", "ping "+userInput).Run()

// SAFE
exec.Command("ping", userInput).Run()
```

### Path Traversal
```go
// VULNERABLE
http.ServeFile(w, r, filepath.Join("/uploads", fileName))

// SAFE
cleaned := filepath.Clean(fileName)
basePath := filepath.Clean("/uploads")
resolved := filepath.Join(basePath, cleaned)
if !strings.HasPrefix(resolved, basePath) {
    http.Error(w, "Invalid path", 400)
    return
}
```

### SSTI (Template Injection)
```go
// VULNERABLE
tmpl := template.Must(template.New("").Parse(userTemplate))

// SAFE — only parse known templates
tmpl := template.Must(template.ParseFiles("templates/welcome.html"))
```

---

## C# / .NET

### SQL Injection
```csharp
// VULNERABLE
string query = $"SELECT * FROM Users WHERE Name = '{name}'";
using var cmd = new SqlCommand(query, conn);

// SAFE — parameterized
string query = "SELECT * FROM Users WHERE Name = @name";
using var cmd = new SqlCommand(query, conn);
cmd.Parameters.AddWithValue("@name", name);
```

### Insecure Deserialization
```csharp
// VULNERABLE
var formatter = new BinaryFormatter();
var obj = formatter.Deserialize(stream);

// SAFE — use JSON
var obj = JsonSerializer.Deserialize<MyType>(json);
```

### XXE
```csharp
// SAFE (XmlReader default is safe in .NET 4.5.2+)
XmlReaderSettings settings = new XmlReaderSettings();
settings.DtdProcessing = DtdProcessing.Prohibit;
settings.XmlResolver = null;
```

---

## PHP

### SQL Injection
```php
// VULNERABLE
$query = "SELECT * FROM users WHERE name = '{$_GET['name']}'";
$result = mysqli_query($conn, $query);

// SAFE — prepared statements
$stmt = $conn->prepare("SELECT * FROM users WHERE name = ?");
$stmt->bind_param("s", $_GET['name']);
$stmt->execute();
```

### XSS
```php
// VULNERABLE
echo $_GET['message'];
echo $userInput;

// SAFE
echo htmlspecialchars($_GET['message'], ENT_QUOTES, 'UTF-8');
```

### File Inclusion
```php
// VULNERABLE
include($_GET['page'] . '.php');
require($_GET['template']);

// SAFE
$allowed = ['home', 'about', 'contact'];
if (in_array($_GET['page'], $allowed)) {
    include($_GET['page'] . '.php');
}
```

### Insecure Deserialization
```php
// VULNERABLE
$obj = unserialize($_COOKIE['user_data']);

// SAFE — use JSON
$data = json_decode($_COOKIE['user_data'], true);
```

---

## Ruby / Rails

### SQL Injection
```ruby
# VULNERABLE
User.where("name = '#{params[:name]}'")
User.where("name = '%s'" % params[:name])

# SAFE
User.where(name: params[:name])
User.where("name = ?", params[:name])
```

### Command Injection
```ruby
# VULNERABLE
system("ping #{user_input}")
`ls #{user_dir}`
exec("convert #{file} output.jpg")

# SAFE
system("ping", user_input)
Open3.capture3("ls", user_dir)
```

### Mass Assignment
```ruby
# VULNERABLE
User.new(params[:user])          # Without strong params

# SAFE
params.require(:user).permit(:name, :email)
```

---

## Quick Detection Grep Patterns by Language

| Language | Grep for Injection | Grep for Secrets | Grep for Unsafe Deserialization |
|----------|--------------------|-----------------------------|-------|
| Python | `execute\(.*[%f{]` / `shell=True` / `jinja2.*\{` | `= ["'].*(?:key|secret|password|token)` | `pickle\.loads` / `yaml\.load` |
| JS/TS | `exec\(` / `eval\(` / `\.innerHTML\s*=` / `\.query\(.*[\$\{\}+]` | Same as above | — |
| Java | `Statement\s+\w+\s*=` / `\+.*query` | Same as above | `ObjectInputStream` / `readObject` |
| Go | `fmt\.Sprintf.*[Qq]uery` / `exec.*sh.*-c` | Same as above | — |
| PHP | `mysql(i)?_query\(.*\$` / `include.*\$` / `require.*\$` | Same as above | `unserialize\(` |
