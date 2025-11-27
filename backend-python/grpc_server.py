import grpc
from concurrent import futures
import time
import predict_pb2
import predict_pb2_grpc
from grracing.models import load_model, load_model_meta, predict
from grracing.data import load_telemetry


class PredictorServicer(predict_pb2_grpc.PredictorServicer):
    def Predict(self, request, context):
        model = load_model(request.model_path)
        meta = load_model_meta(request.model_path)
        df = load_telemetry(request.csv, nrows=1)
        if meta and 'feature_names' in meta:
            feature_names = meta['feature_names']
        else:
            nums = df.select_dtypes(include=['number']).columns.tolist()
            feature_names = nums[:-1] if len(nums) > 1 else nums
        X = [float(df.get(f, 0).fillna(0).iloc[0]) if f in df.columns else 0.0 for f in feature_names]
        preds = predict(model, X)
        return predict_pb2.PredictResponse(prediction=preds, features_used=feature_names)


def serve(host='[::]:50051'):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    predict_pb2_grpc.add_PredictorServicer_to_server(PredictorServicer(), server)
    server.add_insecure_port(host)
    server.start()
    print('gRPC server started on', host)
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == '__main__':
    serve()
