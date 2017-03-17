import pandas as pd

import dataset.metadata
import dataset.utils


def relative_paths(df, target, path, filename, root):
    df[target] = df[path].str.replace(root, "") + df[filename]
    return df.drop([path, filename], axis=1)


def create_metadata_index(config):
    # Load plate maps dataset and create labels
    plate_maps = dataset.metadata.Metadata(
        config["metadata"]["plate_maps"],
        "multi",
        config["metadata"]["platemap_separator"]
    )

    maps = plate_maps.data
    label_field = config["metadata"]["label_field"]
    field1 = config["metadata"]["label_composition"][0]
    field2 = config["metadata"]["label_composition"][1]
    maps[label_field] = maps[field1].astype(str) + "@" + maps[field2].astype(str)

    label_values = maps[label_field].unique()

    print("Unique {}: {}".format(label_field, len(label_values)))
    for i in range(len(label_values)):
        maps.loc[lambda df: df[label_field] == label_values[i], label_field] = i
        dataset.utils.printProgress(i + 1, len(label_values), prefix=label_field)

    # Load barcodes and csv files
    barcodes = dataset.metadata.Metadata(config["original_images"]["barcode_file"], "single")
    load_data = dataset.metadata.Metadata(config["metadata"]["csv_list"], "multi")

    # Merge two frames: csvs + barcodes to attach labels to each image
    columns = list(load_data.data.columns.values)
    metadata = pd.merge(
        load_data.data.drop(columns[13:], axis=1),
        barcodes.data,
        left_on=["Metadata_Plate"],
        right_on=["Assay_Plate_Barcode"],
        how="inner"
    )
    del load_data, barcodes

    # Concatenate paths and filenames and make them relative
    for ch in config["original_images"]["channels"]:
        metadata = relative_paths(
            metadata,
            ch,
            "PathName_Orig" + ch,
            "FileName_Orig" + ch,
            config["original_images"]["path"]
        )
    print(metadata.info())

    # Merge two frames: metadata + plate_maps to attach treatment info to each image
    metadata = pd.merge(
        metadata,
        maps,
        left_on=["Plate_Map_Name", "Metadata_Well"],
        right_on=["plate_map_name", "well_position"],
        how="left"
    )

    # Remove unnecessary columns from the index
    required_columns = ["Metadata_Plate","Metadata_Well","Metadata_Site","Assay_Plate_Barcode","Plate_Map_Name"]
    required_columns += config["original_images"]["channels"] + [label_field]
    available_columns = list(metadata.columns.values)
    columns_to_remove = [c for c in available_columns if c not in required_columns]
    metadata = metadata.drop(columns_to_remove, axis=1)

    # Find replicates
    replicate_field = label_field + "_Replicate"
    metadata["plate_well"] = metadata["Metadata_Plate"].astype(str) + "::" + metadata["Metadata_Well"].astype(str)
    metadata[replicate_field] = 0
    replicate_distribution = {}
    for i in range(len(label_values)):
        mask1 = metadata[label_field] == i
        wells = metadata[mask1]["plate_well"].unique()
        dataset.utils.printProgress(i + 1, len(label_values), "Replicates")
        replicate = 1
        for j in range(len(wells)):
            mask2 = metadata["plate_well"] == wells[j]
            metadata.loc[mask1 & mask2, replicate_field] = replicate
            replicate += 1
        try: replicate_distribution[replicate-1] += 1
        except: replicate_distribution[replicate-1] = 1
    metadata = metadata.drop(["plate_well"], axis=1)
    print(replicate_distribution)

    # Save resulting metadata
    metadata.to_csv(config["metadata"]["filename"], index=False)
    dframe = pd.DataFrame({"ID":pd.Series(range(len(label_values))), "Treatment":pd.Series(label_values)})
    dframe.to_csv(config["metadata"]["labels_file"], index=False)
