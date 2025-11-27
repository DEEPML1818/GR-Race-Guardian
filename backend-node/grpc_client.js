const grpc = require('@grpc/grpc-js');
const protoLoader = require('@grpc/proto-loader');
const path = require('path');

const PROTO_PATH = path.join(__dirname, '..', 'infra', 'predict.proto');

const packageDefinition = protoLoader.loadSync(PROTO_PATH, {
  keepCase: true,
  longs: String,
  enums: String,
  defaults: true,
  oneofs: true
});
const proto = grpc.loadPackageDefinition(packageDefinition).grrg;

function main() {
  const client = new proto.Predictor('localhost:50051', grpc.credentials.createInsecure());
  const req = { model_path: 'backend-python/models/road_america_model.joblib', csv: 'd:\\Working folder with race tracks and timing\\road-america\\road-america\\Road America\\Race 1\\road_america_lap_time_R1.csv' };
  client.Predict(req, (err, resp) => {
    if (err) return console.error('gRPC error', err);
    console.log('Prediction:', resp);
  });
}

if (require.main === module) main();
