import asyncio
import time
import statistics
import httpx


async def fetch(client, url, semaphore):
    """Fetches the URL and returns the status code and latency in milliseconds."""
    async with semaphore:
        start = time.time()
        try:
            response = await client.get(url)
            status = response.status_code
        except Exception:
            status = 500
        latency = (time.time() - start) * 1000
        return status, latency


async def main():
    url = "http://localhost:8000/health"
    total_requests = 1000
    concurrency_limit = 100  # How many requests to send at the exact same time

    print("🚀 Starting load test...")
    print(f"Target: {url}")
    print(f"Total Requests: {total_requests}")
    print(f"Concurrency: {concurrency_limit}\n")

    semaphore = asyncio.Semaphore(concurrency_limit)

    async with httpx.AsyncClient() as client:
        start_time = time.time()

        # Create all the tasks
        tasks = [fetch(client, url, semaphore) for _ in range(total_requests)]

        # Fire them all off concurrently
        results = await asyncio.gather(*tasks)

        total_time = time.time() - start_time

    # Process the results
    latencies = [r[1] for r in results]
    successes = [r[0] for r in results if r[0] == 200]

    # Calculate metrics
    rps = total_requests / total_time
    p50 = statistics.median(latencies)
    p95 = statistics.quantiles(latencies, n=100)[94]
    p99 = statistics.quantiles(latencies, n=100)[98]

    print("-" * 30)
    print("📊 LOAD TEST RESULTS")
    print("-" * 30)
    print(f"Total Time:      {total_time:.2f} seconds")
    print(
        f"Success Rate:    {len(successes) / total_requests * 100:.1f}% ({len(successes)}/{total_requests})"
    )
    print(f"Requests/Second: {rps:.2f} RPS\n")

    print("⏱️  LATENCY METRICS")
    print(f"Average: {statistics.mean(latencies):.2f} ms")
    print(f"p50:     {p50:.2f} ms (50% of requests were faster than this)")
    print(f"p95:     {p95:.2f} ms (95% of requests were faster than this)")
    print(f"p99:     {p99:.2f} ms (99% of requests were faster than this)")
    print(f"Max:     {max(latencies):.2f} ms")


if __name__ == "__main__":
    # Windows requires a specific event loop policy for httpx sometimes
    import sys

    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(main())
