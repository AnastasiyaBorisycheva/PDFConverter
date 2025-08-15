import img2pdf
import os


# convert all files ending in .jpg inside a directory
def image_converter_to_pdf(
        input_directory: str,
        output_directory: str,
        message_id: int) -> str:
    imgs = []
    output_directory = f'{output_directory}/result_{message_id}.pdf'
    file_list = os.listdir(input_directory)
    file_list.sort(key=lambda x: int(x.split('_')[0]))

    for fname in file_list:
        path = os.path.join(input_directory, fname)
        if os.path.isdir(path):
            continue
        imgs.append(path)
    with open(output_directory, "wb") as f:
        f.write(img2pdf.convert(imgs))
    return output_directory
