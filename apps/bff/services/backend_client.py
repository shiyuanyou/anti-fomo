"""
gRPC Client for BFF to communicate with Backend
"""
import grpc
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from shared.proto import service_pb2, service_pb2_grpc


class BackendClient:
    """gRPC client for backend service communication"""

    def __init__(self, backend_addr: str = None):
        if backend_addr is None:
            backend_addr = os.getenv("BACKEND_GRPC_ADDR", "localhost:50051")
        self.backend_addr = backend_addr
        self.channel = None
        self.stub = None

    def connect(self):
        """Establish gRPC connection"""
        if self.channel is None:
            self.channel = grpc.insecure_channel(self.backend_addr)
            self.stub = service_pb2_grpc.PortfolioServiceStub(self.channel)

    def close(self):
        """Close gRPC connection"""
        if self.channel:
            self.channel.close()
            self.channel = None
            self.stub = None

    def get_portfolio(self, user_id: str = "default") -> dict:
        """Get portfolio from backend"""
        try:
            self.connect()
            request = service_pb2.GetPortfolioRequest(user_id=user_id)
            response = self.stub.GetPortfolio(request, timeout=10)
            
            if response.error:
                return {"error": response.error}
            
            return {
                "holdings": [
                    {
                        "symbol": h.symbol,
                        "name": h.name,
                        "weight": h.weight,
                        "value": h.value,
                    }
                    for h in response.holdings
                ],
                "total_value": response.total_value,
            }
        except grpc.RpcError as e:
            return {"error": f"gRPC error: {e.code()}: {e.details()}"}
        except Exception as e:
            return {"error": str(e)}

    def get_market_data(self, symbols: list, period: str = "1y") -> dict:
        """Get market data from backend"""
        try:
            self.connect()
            request = service_pb2.GetMarketDataRequest(
                symbols=symbols,
                period=period
            )
            response = self.stub.GetMarketData(request, timeout=30)
            
            if response.error:
                return {"error": response.error}
            
            return {
                "data": [
                    {
                        "symbol": d.symbol,
                        "name": d.name,
                        "current_price": d.current_price,
                        "change_pct": d.change_pct,
                        "volatility": d.volatility,
                        "market_status": d.market_status,
                    }
                    for d in response.data
                ]
            }
        except grpc.RpcError as e:
            return {"error": f"gRPC error: {e.code()}: {e.details()}"}
        except Exception as e:
            return {"error": str(e)}

    def analyze_with_ai(self, portfolio: dict, market_data: dict, analysis_type: str = "general") -> dict:
        """Request AI analysis from backend"""
        try:
            self.connect()
            
            portfolio_proto = service_pb2.PortfolioResponse(
                holdings=[
                    service_pb2.Holding(
                        symbol=h["symbol"],
                        name=h.get("name", ""),
                        weight=h.get("weight", 0),
                        value=h.get("value", 0),
                    )
                    for h in portfolio.get("holdings", [])
                ],
                total_value=portfolio.get("total_value", 0),
            )
            
            market_proto = service_pb2.MarketDataResponse(
                data=[
                    service_pb2.MarketData(
                        symbol=d["symbol"],
                        name=d.get("name", ""),
                        current_price=d.get("current_price", 0),
                        change_pct=d.get("change_pct", 0),
                        volatility=d.get("volatility", 0),
                        market_status=d.get("market_status", "unknown"),
                    )
                    for d in market_data.get("data", [])
                ]
            )
            
            request = service_pb2.AIAnalyzeRequest(
                portfolio=portfolio_proto,
                market_data=market_proto,
                analysis_type=analysis_type,
            )
            
            response = self.stub.AnalyzeWithAI(request, timeout=60)
            
            if response.error:
                return {"error": response.error}
            
            return {
                "analysis": response.analysis,
                "recommendations": list(response.recommendations),
            }
        except grpc.RpcError as e:
            return {"error": f"gRPC error: {e.code()}: {e.details()}"}
        except Exception as e:
            return {"error": str(e)}

    def run_daily_check(self, force: bool = False) -> dict:
        """Trigger daily check job"""
        try:
            self.connect()
            request = service_pb2.DailyCheckRequest(force=force)
            response = self.stub.RunDailyCheck(request, timeout=30)
            
            return {
                "job_id": response.job_id,
                "status": response.status,
                "message": response.message,
            }
        except grpc.RpcError as e:
            return {"error": f"gRPC error: {e.code()}: {e.details()}"}
        except Exception as e:
            return {"error": str(e)}

    def run_weekly_report(self, force: bool = False) -> dict:
        """Trigger weekly report generation"""
        try:
            self.connect()
            request = service_pb2.WeeklyReportRequest(force=force)
            response = self.stub.RunWeeklyReport(request, timeout=60)
            
            return {
                "job_id": response.job_id,
                "report_id": response.report_id,
                "status": response.status,
                "message": response.message,
            }
        except grpc.RpcError as e:
            return {"error": f"gRPC error: {e.code()}: {e.details()}"}
        except Exception as e:
            return {"error": str(e)}


# Singleton instance
_backend_client = None


def get_backend_client() -> BackendClient:
    """Get singleton backend client"""
    global _backend_client
    if _backend_client is None:
        _backend_client = BackendClient()
    return _backend_client
