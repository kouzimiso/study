import sys
sys.path.append("./Common")
sys.path.append("./Models")
sys.path.append("./ViewModels")
sys.path.append("./Views")
import Scheduler



# Main Program実行部
def main():
    Scheduler.StartUp("Start","RunGame.txt")

if __name__ == "__main__":
    sys.exit(main())
