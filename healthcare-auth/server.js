const http = require('node:http');
const fs = require('node:fs/promises');
const path = require('node:path');
const { URL } = require('node:url');
const { MongoClient } = require('mongodb');

const port = Number(process.env.PORT || 3000);
const root = __dirname;
const databasePath = path.join(root, 'db.json');
const mongoUri = process.env.MONGODB_URI || 'mongodb://localhost:27017/';
const mongoClient = new MongoClient(mongoUri);
let mongoDatabase;
const contentTypes = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8', '.json': 'application/json; charset=utf-8' };

async function readDatabase() {
  return JSON.parse(await fs.readFile(databasePath, 'utf8'));
}

async function writeDatabase(database) {
  await fs.writeFile(databasePath, `${JSON.stringify(database, null, 2)}\n`, 'utf8');
}

async function getCollection(name) {
  if (!mongoDatabase) throw new Error('MongoDB is not connected. Start MongoDB and restart the server.');
  return mongoDatabase.collection(name);
}

async function readRecords(collectionName) {
  return (await getCollection(collectionName)).find({}).project({ _id: 0 }).toArray();
}

async function saveRecord(collectionName, record) {
  const collection = await getCollection(collectionName);
  const key = record.email || record.id || record.name;
  await collection.replaceOne({ _key: key }, { ...record, _key: key }, { upsert: true });
  return record;
}

function sendJson(response, status, body) {
  response.writeHead(status, { 'Content-Type': 'application/json; charset=utf-8' });
  response.end(JSON.stringify(body));
}

const server = http.createServer(async (request, response) => {
  try {
    const requestUrl = new URL(request.url, `http://${request.headers.host}`);
    if (requestUrl.pathname === '/api/accounts' && request.method === 'GET') {
      return sendJson(response, 200, await readRecords('accounts'));
    }
    if (requestUrl.pathname === '/api/accounts' && request.method === 'POST') {
      let body = '';
      for await (const chunk of request) body += chunk;
      const account = JSON.parse(body);
      return sendJson(response, 200, await saveRecord('accounts', account));
    }
    if (requestUrl.pathname === '/api/records' && request.method === 'GET') {
      return sendJson(response, 200, await readRecords(requestUrl.searchParams.get('type')));
    }
    if (requestUrl.pathname === '/api/records' && request.method === 'POST') {
      let body = '';
      for await (const chunk of request) body += chunk;
      const payload = JSON.parse(body);
      return sendJson(response, 200, await saveRecord(payload.type, payload.record));
    }

    const relativePath = requestUrl.pathname === '/' ? 'index.html' : requestUrl.pathname.slice(1);
    const filePath = path.resolve(root, relativePath);
    if (!filePath.startsWith(root) || request.method !== 'GET') return sendJson(response, 404, { error: 'Not found' });
    const content = await fs.readFile(filePath);
    response.writeHead(200, { 'Content-Type': contentTypes[path.extname(filePath)] || 'application/octet-stream' });
    response.end(content);
  } catch (error) {
    sendJson(response, error.code === 'ENOENT' ? 404 : 500, { error: error.message });
  }
});

mongoClient.connect()
  .then(() => {
    mongoDatabase = mongoClient.db('carepoint');
    server.listen(port, () => console.log(`Carepoint running at http://localhost:${port}`));
  })
  .catch((error) => {
    console.error(`MongoDB connection failed: ${error.message}`);
    process.exitCode = 1;
  });
