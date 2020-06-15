import sys
from test import dataset, detector

if __name__ == "__main__":
    if sys.argv[1] == "--test":
        if sys.argv[2] == 'wheel':
            pass

    elif sys.argv[1] == '--dataset':
        if sys.argv[2] == 'mining':
            dataset.mining()
        if sys.argv[2] == 'show_info':
            dataset.show_info()
        if sys.argv[2] == 'view_samples':
            dataset.view_samples()

    elif sys.argv[1] == '--detector':
        if sys.argv[2] == 'mobilenet':
            detector.mobilenet()
        if sys.argv[2] == 'summary':
            detector.summary()
        if sys.argv[2] == 'show_predictions':
            detector.show_predictions()
        if sys.argv[2] == 'train':
            detector.train()
        if sys.argv[2] == 'predict':
            detector.predict()
        if sys.argv[2] == 'convert':
            detector.convert()
        if sys.argv[2] == 'infer':
            detector.infer()

    else:
        print("Error: Invalid option!")
