import subprocess
import sys
import time

def stop_bitcoin_tracker():
    """Stop all Bitcoin tracker processes"""
    print("Stopping Bitcoin Price Tracker...")
    
    try:
        # Kill Python processes (be careful with this on systems with other Python apps)
        result = subprocess.run([
            "taskkill", "/f", "/im", "python.exe"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Python processes terminated")
        else:
            print("⚠️  No Python processes found or already stopped")
    
    except Exception as e:
        print(f"❌ Error stopping processes: {e}")
    
    # Also try to stop Streamlit specifically
    try:
        result = subprocess.run([
            "taskkill", "/f", "/fi", "WINDOWTITLE eq Streamlit*"
        ], capture_output=True, text=True)
    except:
        pass
    
    print("🛑 Stop command completed")
    print("You may need to manually close browser tabs if they're still open")

if __name__ == "__main__":
    stop_bitcoin_tracker()