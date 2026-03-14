"""
gRPC Service Implementation for Backend
"""
import grpc
from concurrent import futures
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from shared.proto import service_pb2, service_pb2_grpc


class PortfolioServicer(service_pb2_grpc.PortfolioServiceServicer):
    """Implementation of PortfolioService gRPC service"""

    def GetPortfolio(self, request, context):
        """Get portfolio data"""
        try:
            return service_pb2.PortfolioResponse(
                holdings=[],
                total_value=0.0,
                error="Not implemented yet"
            )
        except Exception as e:
            return service_pb2.PortfolioResponse(error=str(e))

    def GetMarketData(self, request, context):
        """Get market data for symbols"""
        try:
            return service_pb2.MarketDataResponse(
                data=[],
                error="Not implemented yet"
            )
        except Exception as e:
            return service_pb2.MarketDataResponse(error=str(e))

    def AnalyzeWithAI(self, request, context):
        """Analyze portfolio with AI"""
        try:
            return service_pb2.AIAnalyzeResponse(
                analysis="AI analysis not implemented yet",
                recommendations=[],
                error="Not implemented yet"
            )
        except Exception as e:
            return service_pb2.AIAnalyzeResponse(error=str(e))

    def GenerateReport(self, request, context):
        """Generate report"""
        try:
            return service_pb2.ReportResponse(
                report_id="",
                title="",
                content="",
                error="Not implemented yet"
            )
        except Exception as e:
            return service_pb2.ReportResponse(error=str(e))

    def RunDailyCheck(self, request, context):
        """Run daily check job"""
        try:
            return service_pb2.DailyCheckResponse(
                job_id="",
                status="not_implemented",
                message="Daily check not implemented yet"
            )
        except Exception as e:
            return service_pb2.DailyCheckResponse(
                job_id="",
                status="error",
                message=str(e)
            )

    def RunWeeklyReport(self, request, context):
        """Run weekly report job"""
        try:
            return service_pb2.WeeklyReportResponse(
                job_id="",
                report_id="",
                status="not_implemented",
                message="Weekly report not implemented yet"
            )
        except Exception as e:
            return service_pb2.WeeklyReportResponse(
                job_id="",
                report_id="",
                status="error",
                message=str(e)
            )


def serve(port=50051):
    """Start gRPC server"""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    service_pb2_grpc.add_PortfolioServiceServicer_to_server(
        PortfolioServicer(), server
    )
    server.add_insecure_port(f'[::]:{port}')
    server.start()
    print(f"gRPC server started on port {port}")
    server.wait_for_termination()


if __name__ == '__main__':
    serve()
