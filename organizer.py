import asyncio
import time
import json
from api.wallpaper_api import WallpaperAPI, ImageItem, DownloadItem
from utility import type_imagine, download_and_convert_image, upload_to_firebase_3, initialize_firebase, safe_delete, click_somewhere, is_macos, resize_image, download_image, resize_all_and_upload_to_firebase, blur_image, resize_one_blur_and_upload_to_firebase

api_client = WallpaperAPI()

# Down size image test, Run the async main function

async def downsize_all_images(item_id, thumbnail):
    # Download the thumbnail image
    target_local_file = await download_image(thumbnail)

    imageList_Result = resize_all_and_upload_to_firebase(target_local_file)

    return imageList_Result

    # # Resize the image to different resolutions
    # LD_file_path, LD_resolution = await resize_image(target_local_file, "LD", 0.25)
    # SD_file_path, SD_resolution = await resize_image(target_local_file, "SD", 0.5)
    # HD_file_path, HD_resolution = await resize_image(target_local_file, "HD", 1.0)

    # # Upload resized images to Firebase
    # LD_firebase_url, LD_blob_name = upload_to_firebase_3(LD_file_path, "LD", LD_resolution)
    # SD_firebase_url, SD_blob_name = upload_to_firebase_3(SD_file_path, "SD", SD_resolution)
    # HD_firebase_url, HD_blob_name = upload_to_firebase_3(HD_file_path, "HD", HD_resolution)

    # # You can add code to delete the local files here
    # safe_delete(LD_file_path)
    # safe_delete(SD_file_path)
    # safe_delete(HD_file_path)
    # safe_delete(target_local_file)

    # # Create image list as a list of dictionaries (proper JSON structure)
    # image_list = [
    #     {
    #         "type": "LD",
    #         "resolution": LD_resolution,
    #         "link": LD_firebase_url,
    #         "blob": LD_blob_name
    #     },
    #     {
    #         "type": "SD",
    #         "resolution": SD_resolution,
    #         "link": SD_firebase_url,
    #         "blob": SD_blob_name
    #     },
    #     {
    #         "type": "HD",
    #         "resolution": HD_resolution,
    #         "link": HD_firebase_url,
    #         "blob": HD_blob_name
    #     }
    # ]



async def main():
    try:
        initialize_firebase()
    except Exception as e:
        print(f"initialize_firebase Error: {str(e)}")

    result = api_client.get_wallpapers()

    #print("result=")
    #print(result)
    total_items = 0
    test_index = 0
    # Extract data from the result
    try:
        # Clean the message string and parse JSON
        message_str = result.get('message', '').strip()
        wallpapers = json.loads(message_str)

        if isinstance(wallpapers, list):
            total_items = len(wallpapers)
            print(f"Total: {len(wallpapers)}")
        else:
            print("Error: 'wallpapers' is not a list.")

        print("\n=== EXTRACTED DATA ===")
        for item in wallpapers:
            test_index += 1

            # Get thumbnail
            thumbnail = item.get('thumbnail', 'N/A')

            # Get first name from imageList
            image_list = item.get('imageList', [])
            first_image_name = "N/A"
            if image_list and len(image_list) > 0:
                first_image_name = image_list[0].get('type', 'N/A')

            item_id = item.get('itemId', '0')

            print("-" * 50)
            #print(f"\nitemId: {item_id}")
            #print(f"Thumbnail: {thumbnail}")
            #print(f"First ImageList Name: {first_image_name}")

            if first_image_name == "LD":
                print(f"({test_index} / {total_items}) This item has been updated: {item_id}")
                continue
            elif first_image_name == "small": # old data, need to update
                print(f"\n ({test_index} / {total_items}) Start to update image_list, itemId=:{item_id} \n")

                updated_data = await downsize_all_images(item_id, thumbnail)

                #print(updated_data)

                # Call the API and check the response
                response = api_client.patch_data_by_field(item_id, "imageList", updated_data)

                # Check if the API call was successful
                if not response.get('success', False):
                    print(f"API call failed: {response.get('message', 'Unknown error')}")
                    break  # Break the loop if the API call failed
                else:
                    print(f"Successfully updated imageList for item {item_id}")

            else:
                print(f"Error first_image_name or item_id {item_id}")
                break

    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
    except Exception as e:
        print(f"Error processing data: {e}")


async def test_area():
    test = "https://firebasestorage.googleapis.com/v0/b/palettex-37930.appspot.com/o/images%2Fthumbnail%2F20250305_055540_thumbnail_8ae9af09-a8ac-4b14-a72c-cec1701b7905.jpg?alt=media"

    target_local_file = await download_image(test)

    LD_file_path, LD_resolution = await resize_image(target_local_file, "BL", 0.25, reduce_quality=100)
    BLUR_file_path, BLUR_resolution = blur_image(LD_file_path, "BL", blur_strength=32)

async def add_blur_to_all_wallpapers():
    try:
        initialize_firebase()
    except Exception as e:
        print(f"initialize_firebase Error: {str(e)}")

    result = api_client.get_wallpapers()
    test_index = 0

    try:
        message_str = result.get('message', '').strip()
        wallpapers = json.loads(message_str)

        if isinstance(wallpapers, list):
            print(f"Total: {len(wallpapers)}")

        print("\n=== ADDING BLUR IMAGES ===")
        for item in wallpapers:
            test_index += 1

            item_id = item.get('itemId', '0')
            thumbnail = item.get('thumbnail', 'N/A')

            # Download thumbnail and create blur version
            target_local_file = await download_image(thumbnail)

            # This should return a dict with type, resolution, link, blob
            updated_data = await resize_one_blur_and_upload_to_firebase(target_local_file)

            # Add the BL image to existing imageList
            response = api_client.add_one_image_list_item(item_id, "imageList", updated_data)

            if not response.get('success', False):
                print(f"Failed to add blur image for item {item_id}")
                print(f"API call failed: {response.get('message', 'Unknown error')}")
                break
            else:
                print(f"✓ Successfully added blur image to item {item_id} ({test_index}/{len(wallpapers)})")

            # if test_index >= 2:
            #     print(f" ===== TEST break =====")
            #     break

    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
    except Exception as e:
        print(f"Error processing data: {e}")


if __name__ == "__main__":
    # asyncio.run(main())                   # Transfer old data and update all imageList
    # asyncio.run(test_area())              # test generate blur image
    asyncio.run(add_blur_to_all_wallpapers())   # Generate all blur to database