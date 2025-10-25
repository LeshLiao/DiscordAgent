import asyncio
import time
import json
import os
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

async def download_all_images_by_type(type="BL", file_name_prefix="images_"):
    """
    Download all images of a specific type from the database to the output folder.
    Adds a prefix combining file_name_prefix + type to each filename.

    Args:
        type (str): Image type to download. Options: "BL", "LD", "SD", "HD"
                   Default is "BL" (blur)
        file_name_prefix (str): Prefix to add before the type and filename.
                               Default is "images_"

    Examples:
        # Download BL images with "images_BL_" prefix
        await download_all_images_by_type(type="BL", file_name_prefix="images_")
        Result: images_BL_20251025_075513_BL_204x364_7bf3370b-8bed-46e3-a996-8c96208779be.jpg
    """
    try:
        # Combine prefix with type to create final prefix
        final_prefix = f"{file_name_prefix}{type}_"

        # Create output directory with type-specific subfolder
        output_dir = f"output/{type.lower()}_images"
        os.makedirs(output_dir, exist_ok=True)

        print(f"Output directory: {output_dir}")
        print(f"Image type: {type}")
        print(f"Base prefix: '{file_name_prefix}'")
        print(f"Final prefix: '{final_prefix}'")

        # Get all wallpapers from the API
        result = api_client.get_wallpapers()

        message_str = result.get('message', '').strip()
        wallpapers = json.loads(message_str)

        if not isinstance(wallpapers, list):
            print("Error: 'wallpapers' is not a list.")
            return

        total_items = len(wallpapers)
        print(f"Total wallpapers: {total_items}")

        # Counters
        downloaded_count = 0
        skipped_count = 0
        error_count = 0
        no_image_count = 0

        print(f"\n=== DOWNLOADING {type} IMAGES ===")

        for index, item in enumerate(wallpapers, 1):
            # if index > 2:
            #     print(f" ===== TEST break =====")
            #     break

            item_id = item.get('itemId', 'unknown')
            image_list = item.get('imageList', [])

            # Find the image with the specified type
            target_image = None
            for img in image_list:
                if img.get('type') == type:
                    target_image = img
                    break

            if not target_image:
                # Only show message for first few items to avoid spam
                if no_image_count < 5 or index % 50 == 0:
                    print(f"({index}/{total_items}) ⊘ No {type} image found for item {item_id}")
                no_image_count += 1
                continue

            # Get the image URL and blob path
            image_url = target_image.get('link')
            blob_path = target_image.get('blob', '')

            if not image_url:
                print(f"({index}/{total_items}) ✗ No link found for {type} image in item {item_id}")
                error_count += 1
                continue

            try:
                # Extract original filename from blob path
                if blob_path:
                    # Example blob: "images/BL/20250228_145732_BL_xxx.jpg"
                    original_filename = os.path.basename(blob_path)
                else:
                    # Fallback: try to extract from URL
                    from urllib.parse import urlparse, unquote
                    parsed_url = urlparse(image_url)
                    path = unquote(parsed_url.path)

                    if '/o/' in path:
                        filename_with_path = path.split('/o/')[-1].split('?')[0]
                        filename_with_path = unquote(filename_with_path)
                        original_filename = os.path.basename(filename_with_path)
                    else:
                        # Last resort: use itemId with type
                        file_extension = '.jpg'
                        original_filename = f"{item_id}_{type}{file_extension}"

                # Add final prefix (base prefix + type + underscore) to the filename
                prefixed_filename = f"{final_prefix}{original_filename}"

                # Full path for the final destination
                final_output_path = os.path.join(output_dir, prefixed_filename)

                # Check if file already exists
                if os.path.exists(final_output_path):
                    if skipped_count < 5 or index % 50 == 0:
                        print(f"({index}/{total_items}) ⊙ Already exists: {prefixed_filename}")
                    skipped_count += 1
                    continue

                # Download using existing utility function
                temp_downloaded_path = await download_image(image_url)

                # Move/rename to our target location with prefixed filename
                import shutil
                shutil.move(temp_downloaded_path, final_output_path)

                print(f"({index}/{total_items}) ✓ Downloaded: {prefixed_filename}")
                downloaded_count += 1

            except Exception as e:
                print(f"({index}/{total_items}) ✗ Error downloading {item_id}: {str(e)}")
                error_count += 1
                continue

        # Summary
        print("\n" + "=" * 50)
        print("DOWNLOAD SUMMARY")
        print("=" * 50)
        print(f"Image type:        {type}")
        print(f"Total wallpapers:  {total_items}")
        print(f"✓ Downloaded:      {downloaded_count}")
        print(f"⊙ Skipped:         {skipped_count}")
        print(f"⊘ No {type} image:   {no_image_count}")
        print(f"✗ Errors:          {error_count}")
        print(f"\nFilename format: {final_prefix}[original_name].jpg")
        print(f"All {type} images saved to: {output_dir}")

    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
    except Exception as e:
        print(f"Error in download_all_images_by_type: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # asyncio.run(main())                       # Transfer old data and update all imageList
    # asyncio.run(test_area())                  # test generate blur image
    # asyncio.run(add_blur_to_all_wallpapers())   # Generate all blur to database

    # Download BL (blur) images - default settings
    asyncio.run(download_all_images_by_type(type="BL", file_name_prefix="images_"))