import pyautogui
import time

def click_somewhere(image_file):
    # Locate the image on the screen
    location = pyautogui.locateOnScreen(image_file, confidence=0.8)
    if location:
        print("Image found!")
        # Get the center of the located image
        center = pyautogui.center(location)

        # Adjust for Retina display by dividing coordinates by 2
        adjusted_center = (center[0] / 2, center[1] / 2)  # on macOS (Retina displays)
        print(f"Adjusted Center: {adjusted_center}")

        # Click the adjusted center of the image
        pyautogui.click(adjusted_center)
        time.sleep(1)
        pyautogui.click(adjusted_center)
    else:
        print("Image not found on the screen.")

# Usage example:
if __name__ == "__main__":
    click_somewhere("img/Message_upscale_textbox.png")