import os
# import httpx
# import mcp
from mcp.server.fastmcp import FastMCP

# Proceed with importing your module
from tool_sample.run_realtime_report import GoogleAnalyticsRealTimeReport


# initialize authentication
from google.oauth2 import service_account
from dotenv import load_dotenv

load_dotenv()

credentials_file = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
credentials = service_account.Credentials.from_service_account_file(
    credentials_file
    )

# Initialize FastMCP server
mcp = FastMCP(
    name="Google Analytics 4",
    host="127.0.0.1",
    port=5000,
    timeout=30
    )


@mcp.tool()
def get_realtime_report(
    property_id: str,
    metrics: list,
    dimensions: list = None
) -> str:
    """Returns real-time data from Google Analytics 4.   
    Args:
        property: A Google Analytics GA4 property identifier (e.g., "123456789")
        metrics: Metrics attributes for real-time data. Examples: "activeUsers", "screenPageViews"
        dimensions: Optional dimension attributes. Examples: "city", "browser"
    """

    real_time_report = GoogleAnalyticsRealTimeReport(credentials)
    return real_time_report.run_realtime_report(property_id, metrics, dimensions)



if __name__ == "__main__":
    mcp.run(transport="stdio")
