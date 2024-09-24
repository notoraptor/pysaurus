# 2024/09/07

## Tried sentence-transformers to find similar thumbnails

Tried: https://stackoverflow.com/a/71567609

Seems too slow for what I want 
(adding all database images in model takes too much time, I don't know why).

````python
from sentence_transformers import SentenceTransformer, util

from other.other_tests.local_image_provider import LocalImageProvider
from pysaurus.core.informer import Informer


def main():
    imp = LocalImageProvider()
    image_names = []
    images = []
    for filename, image in imp.items():
        image_names.append(filename)
        images.append(image.resize((32, 32)))

    # Load the OpenAI CLIP Model
    print("Loading CLIP Model...")
    model = SentenceTransformer("clip-ViT-B-32")

    # Next we compute the embeddings
    # To encode an image, you can use the following code:
    # from PIL import Image
    # encoded_image = model.encode(Image.open(filepath))
    print("Images:", len(image_names))
    encoded_image = model.encode(
        images, batch_size=128, convert_to_tensor=True, show_progress_bar=True
    )

    # Now we run the clustering algorithm. This function compares images against
    # all other images and returns a list with the pairs that have the highest
    # cosine similarity score
    processed_images = util.paraphrase_mining_embeddings(encoded_image)
    NUM_SIMILAR_IMAGES = 10

    # =================
    # DUPLICATES
    # =================
    print("Finding duplicate images...")
    # Filter list for duplicates.
    # Results are triplets (score, image_id1, image_id2) and is scorted in decreasing order
    # A duplicate image will have a score of 1.00
    duplicates = [image for image in processed_images if image[0] >= 1]

    # Output the top X duplicate images
    for score, image_id1, image_id2 in duplicates[0:NUM_SIMILAR_IMAGES]:
        print("\nScore: {:.3f}%".format(score * 100))
        print(image_names[image_id1])
        print(image_names[image_id2])

    # =================
    # NEAR DUPLICATES
    # =================
    print("Finding near duplicate images...")
    # Use a threshold parameter to identify two images as similar.
    # By setting the threshold lower, you will get larger clusters
    # which have less similar images in it. Threshold 0 - 1.00
    # A threshold of 1.00 means the two images are exactly the same.
    # Since we are finding near duplicate images,
    # we can set it at 0.99 or any number 0 < X < 1.00.
    threshold = 0.99
    near_duplicates = [image for image in processed_images if image[0] < threshold]

    for score, image_id1, image_id2 in near_duplicates[0:NUM_SIMILAR_IMAGES]:
        print("\nScore: {:.3f}%".format(score * 100))
        print(image_names[image_id1])
        print(image_names[image_id2])


if __name__ == '__main__':
    Informer.contextualize(main)
````
