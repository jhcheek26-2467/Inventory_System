import os
import win32com.client

# Update this path before running (Windows path, not WSL)
DOWNLOAD_DIR = r"C:\Users\jhcheek\Downloads\partender_exports"

# Name of the Outlook mail folder to search (must match exactly)
FOLDER_NAME = "Partender Exports"

# Connect to the Outlook application already running on Windows (or start it)
outlook = win32com.client.Dispatch("Outlook.Application")

# MAPI is Outlook's mail API; "MAPI" is the standard namespace name
namespace = outlook.GetNamespace("MAPI")

# Walk every folder in every mailbox until we find "Partender Exports"
target_folder = None
folders_to_check = []

# namespace.Folders holds top-level stores (e.g. your mailbox, archives)
for i in range(1, namespace.Folders.Count + 1):
    folders_to_check.append(namespace.Folders.Item(i))

# Breadth-first search: check each folder, queue its subfolders
while folders_to_check:
    folder = folders_to_check.pop(0)

    if folder.Name == FOLDER_NAME:
        target_folder = folder
        break

    # Outlook folder collections are 1-indexed, not 0-indexed
    for j in range(1, folder.Folders.Count + 1):
        folders_to_check.append(folder.Folders.Item(j))

if target_folder is None:
    raise RuntimeError(f'Outlook folder not found: "{FOLDER_NAME}"')

# Create the download folder if it does not exist yet
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

downloaded = 0
skipped = 0

# Loop through every email in the target folder
messages = target_folder.Items
for i in range(1, messages.Count + 1):
    message = messages.Item(i)

    # Some folder items are not mail (meetings, etc.) — skip those safely
    if not hasattr(message, "Attachments"):
        continue

    attachments = message.Attachments
    for j in range(1, attachments.Count + 1):
        attachment = attachments.Item(j)
        filename = attachment.FileName

        # Only Excel files whose name contains "Inventory" (Partender export pattern)
        if not filename.lower().endswith(".xlsx"):
            continue
        if "Inventory" not in filename:
            continue

        dest_path = os.path.join(DOWNLOAD_DIR, filename)

        # Do not overwrite files already downloaded
        if os.path.exists(dest_path):
            print(f"SKIP  {filename} (already exists)")
            skipped += 1
            continue

        # SaveAsFile writes the attachment bytes to disk
        attachment.SaveAsFile(dest_path)
        print(f"SAVE  {filename}")
        downloaded += 1

print()
print("Summary")
print(f"  Downloaded: {downloaded}")
print(f"  Skipped:    {skipped}")
