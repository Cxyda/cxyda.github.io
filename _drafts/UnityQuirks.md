# Leveraging `?.`, `??`, and `==` Operators in Unity and C#: The Good, the Bad, and the Gotchas

C# is a versatile language offering syntactic sugar and expressive tools that make code concise, readable, and functional. Among its arsenal are the `?.`, `??`, and `==` operators, which serve distinct purposes in handling nullability, default values, and equality. While these tools are incredibly useful, their behavior in Unity—especially when dealing with `UnityEngine.Object` derivatives—comes with unique caveats and potential pitfalls.

This article explores the purpose of these operators, the pros and cons of using them in Unity projects, and specific pitfalls when working with Unity objects like GameObjects, MonoBehaviours, and ScriptableObjects.

---

## Understanding the `==` Operator (Equality Comparison)

The `==` (equality comparison) operator in C# checks for value equality in value types and reference equality in reference types. Unity, however, overrides this behavior for objects deriving from `UnityEngine.Object`. Which in some cases can lead to unexpected behavior. Unity does not only check reference equality for reference type objects, but also does some "quality of life" checks to reduce boilerplate code and trying to prevent developers from common pitfalls.

### The `==` Operator in Unity

```csharp
private void Start()
{
	GameObject obj = new GameObject("Test");
	Destroy(GameObject);

	// This will log "false". The object has been marked for destruction but the object is not null yet (will be cleaned up later in that frame)
	Debug.Log($"Is UnityEngine.Object obj == null? {_obj == null}}"); 
	// This also will log "false" for the same reason.  
	Debug.Log($"Is C# object obj is null? System.Object.ReferenceEquals(_obj, null)}"); 

	// The object is not null, therefore the following code will be executed
	if (obj != null)
	{  
	// This will log "The name of the obj is Test" to the console since the object has not yet been destroyed.  
	    Debug.Log($"The name of the obj is {obj.name}"); 
	}
}

private void Update()  
{
	// Here the Unity quirks begin ...
	
	// This will log "true" due to Unity doing additional null checks. The underlying objects is actually not null but the reference to it is gone now.
	Debug.Log($"Is UnityEngine.Object obj == null? {obj == null}}"); 
	// But using standard C# this will log "false".
	Debug.Log($"Is C# object obj is null? System.Object.ReferenceEquals(obj, null)}"); 
	if (obj != null) // This is safe to do, in the Unity world this evaluates as false and the following code won't be executed
	{  
		// This won't be executed
	    Debug.Log($"The name of the obj is {obj.name}"); 
	}
}
``` 

As you can see, the madness starts in the `Update()` method. By overriding the `==` operator protects the developer from doing mistakes. The object which we marked for destruction at the beginning of the frame is now destroyed. But until the garbage collector kicks in and fully cleans the object, the object is actually not null, but the reference to it is gone. Normally the developer does not care about that and is mainly interested in "can I access the object?".  Therefore, thanks Unity for doing that - good job!

But with the introduction of C# version 6.0 and the official support by Unity new language features were introduced to C#. These were for example the null conditional ( `?.`) and the null coalescing (`??`) operators. These are with us since quite some time and I think I can safely say it is quite commonly used Unity code bases. This is why in my opinion every Unity developer should know about the problems that can arise using it. In contrast to the `==` (and the `!=`) operator, these operators can not overwritten and this is where the madness begins ...

---
## Understanding the `?.` Operator (Null Conditional)

The `?.` (null conditional) operator lets you call methods or access properties only if the left-hand object is not null. If the object is null, the operation short-circuits and returns null instead of throwing an exception. This operator can not be overwritten in the C# language.

### Standard C# Example

``` csharp
Player player = null; // Safely access the player's name
string playerName = player?.Name; // Returns null without throwing an exception
```

This operator is often used in method chains and when dealing with optional or nullable objects.

### The `?.` Operator in Unity

Since this operator can not be overridden in C#, Unity can not provide us with quality of life features that help us using this in the Unity world. Let's use the same example as we did above. Nothing changes in the `Start()` method we are free to use the `?.` operator there.

```csharp

private void Start()
{
	GameObject obj = new GameObject("Test");  
	Object.Destroy(obj);
	Debug.Log(obj?.name); // Will log "Test"
}

```

In the `Update()` method however life gets a little more complicated.

``` csharp
private void Update()  
{
	if (obj != null) // This is safe to do, in the Unity world this evaluates as false and the following code won't be executed
	{  
		// This won't be executed
	    Debug.Log($"The name of the obj is {obj.name}"); 
	}
	
	// Using the null conditional operator `?.` here will throw a MissigReferenceException since the reference to that object is gone.
	Debug.Log(obj?.name); 
}

```

In this example the GameObject has been marked for destruction earlier that frame. In `Update()` the Unity has destroyed the GameObject but the underlying C# object has not yet been cleaned up by the Garbage Collector. Therefore accessing the object with the supposedly safe null conditional operator throws a MissingReferenceException.

---

## Understanding the `??` Operator (Null Coalescing)

The `??` operator simplifies null-checking by returning the left-hand operand if it’s not null, or the right-hand operand otherwise. This operator can not be overwritten in the C# language.

### Standard C# Example

```csharp
	string playerName = null;
	string displayName = playerName ?? "Unknown Player";
```

### The `??` Operator in Unity

In Unity, the `??` operator can streamline null-coalescing checks for scripts, components, or optional references. For instance:


```csharp
AudioSource audioSource = GetComponent<AudioSource>() ?? GameObject.AddComponent<AudioSource>();
```

This makes for cleaner code compared to a more verbose `if`-`else` construct. But since this operator can also not be overridden in C#, Unity can not provide us with quality of life features that help us using this in the Unity world neither due to the fact that the `??` operator does as well not respect `UnityEngine.Object` lifecycles. Using this is not as dangerous as using `?.` since to my knowledge there is no pattern which could throw an exception directly. But it can result in exceptions later when the object is not identified as being null soon.

```csharp

[SerializeField] private SomeScript _someScript;  
  
private void Awake()  
{  
    DestroyImmediate(_someScript);
	// It won't be recognized here that the component will be gone soon and therefore not assigned
	_someScript = _someScript ?? gameObject.AddComponent(typeof(SomeScript)) as SomeScript;  
}  
  
private void Start()  
{  
	_someScript.DoSomething();  // This will throw an exception since the component has not been assigned again
}

```

I agree that this is a very constructed example and using this fails in a lot less cases than using the `?.` operator. But depending on where and how you use it, it can fail for Unity Objects.

---

## Conclusion

As you can see, it is very context dependent whether you can use the `?.` and `??` operators safely on UnityObjects or not. You might say after reading this article you understood everything about it and now you can use it safely. But what if you are working in a bigger, professional teams where  code is constantly changing, other developers contribute and start mimicking what you did without understanding it fully or when using external plugins where you cannot be sure what is happening? This in my opinion renders the usage of `?.` and `??` as very fragile and should generally be avoided for objects derived from `UnityEngine.Object`. But on plain C# objects they provide a lot of benefits like concise and readable code as well as null-safe operations.