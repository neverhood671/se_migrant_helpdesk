# Topic recognition model

The sklearn kmeans model trained on the [dataset](..%2Fdata%2Fgenerated_questions.csv).

## Model usage

1. Unzip [model.zip](model.zip)
2. Load model and vectoraizer

    ```python
    import pickle
    
    with open('model_kmeans' , 'rb') as f:
        kmeans = pickle.load(f)
    
    with open('model_vectorizer' , 'rb') as f:
        vectorizer = pickle.load(f)
    ```

3. Vectorize your text and get its topic prediction
    ```python
    test = ['I want to start SFI']
    test_vec = vectorizer.transform(test)  
    res = kmeans.predict(test_vec)
    ```
   
## Topics
```
0 - swedish
1 - bank
2 - pn
3 - apartment
4 - culture
```