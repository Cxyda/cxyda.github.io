---
layout: post
title: Mastering C# Operators in Unity ?., ??, ==
tags: [C#,Unity3D]
# lastmod: 2024-11-14
---

C# is a powerhouse language ⚡, offering an array of features like **syntactic sugar** and expressive tools that make your code concise, readable, and functional. Among these gems are the **`?.`**, **`??`**, and **`==`** operators—designed to handle nullability, default values, and equality with elegance. ✨  

But here’s the twist: when Unity enters the chat, things get... *interesting*. 😅 Unity’s handling of `UnityEngine.Object` derivatives (GameObjects, MonoBehaviours, ScriptableObjects, etc.) adds unique nuances—and even potential pitfalls—to these operators’ behavior. This post dives into their quirks, benefits, and challenges in Unity’s world. 🛠️  

---

## **The `==` Operator: Equality in C# vs. Unity**  

In standard C#, the `==` operator checks for **value equality** in value types and **reference equality** in reference types. Sounds simple, right? Not so fast! 🛑 Unity overrides this operator for objects derived from `UnityEngine.Object`. While this adds developer-friendly "quality of life" features 🛡️, it can also lead to surprising results.  

---

### **Unity’s Take on `==`**  

Let’s unravel the mystery with some code:  

{% gist 67224a2fe58e9f387943c50e06a5f9b0 %}  

As the code shows, things get... *weird* in the `Update()` method. By overriding the `==` operator, Unity shields you from common mistakes. 🙌  

Here’s what happens:  
- At the start of the frame, the object is marked for destruction.  
- The underlying C# object isn’t technically `null` yet—the garbage collector hasn’t cleaned it up.  
- Unity steps in and pretends the object is null when you try to access it, ensuring that your code doesn’t crash.  

💡 **TL;DR**: Unity’s `==` operator checks if the object is accessible rather than strictly null, making life easier for developers. Good job, Unity! 👏  

But... what happens when 'newer' (introduced in 2015) C# features like `?.` and `??` enter the equation? These operators can’t be overridden, and therein lies the chaos. 🌀  

---

## **The `?.` Operator: Null-Conditional Access**  

The `?.` operator is a C# favorite for null-safe access. It allows you to call methods or properties **only if the left-hand object isn’t null**. Otherwise, it short-circuits and returns `null`—no exceptions, no drama. 🎭  

But wait... Unity doesn’t play by the same rules here. 😬  

---

### **Standard C# Example**  

{% gist 54fe7a3da4e3d95f301a3fd43f37eb13 example.cs %}  

This operator shines when dealing with nullable or optional objects in vanilla C#. It keeps your code clean and crash-free. 🚿  

---

### **The `?.` Operator in Unity**  

In Unity, the null-conditional operator becomes a little tricky:  

{% gist 06591e1418084be30b8356183d0ff571 example.cs %}  

In the `Start()` method, everything works fine. Unity is happy, and the `?.` operator behaves as expected. But in the **`Update()` method**, all bets are off. 🎲  

{% gist f2ffe42b7ccfe676b508937da7dd91fe %}  


- If the GameObject was destroyed earlier that frame, Unity’s `==` operator would have protected you.  
- But the `?.` operator **doesn’t respect Unity’s lifecycle magic**, leading to a `MissingReferenceException`.  

Unity’s overridden behavior doesn’t extend to operators it can’t control, making `?.` risky for `UnityEngine.Object` derivatives. Proceed with caution! 🚧  

---

## **The `??` Operator: Null-Coalescing Awesomeness**  

The `??` operator is a lifesaver for null-checks. It returns the left-hand operand if it’s not null or the right-hand operand otherwise. **Simple, powerful, and concise.** 💪  

---

### **Standard C# Example**  

{% gist 9057a8a1b63df416c22979b66d9e21f4 %}  

In pure C#, the `??` operator is a great way to handle optional values or provide fallbacks with minimal verbosity.  

---

### **The `??` Operator in Unity**  

{% gist 924684a6ca1b9c83b9927853506fade6 %}  

Here, the `??` operator simplifies fallback logic for Unity objects like scripts, components, or optional references. But it has one major caveat:  

- Like the `?.` operator, the `??` operator **doesn’t respect Unity’s lifecycle quirks**.  
- While it’s less likely to throw immediate exceptions, it can cause subtle bugs if the object was destroyed but not yet cleaned up by the GC.  

{% gist 5cbd59d2b96861b470200b9f377ef3a9 %}  

This contrived case shows how the `??` operator could lead to unexpected behavior when working with Unity objects.  

💡 **Pro Tip**: Stick to traditional null-checks (`if`-`else`) for `UnityEngine.Object` types to avoid surprises.  

---

## **Conclusion: Use with Caution! ⚠️**  

Operators like `?.` and `??` are fantastic tools working with regular C# objects, making code cleaner, more concise, and less error-prone. But in Unity’s ecosystem, they can introduce subtle, hard-to-diagnose bugs. 🐛  

Here’s the golden rule:  
- **For Unity objects (`UnityEngine.Object` derivatives)**: Avoid using `?.` and `??` operators. Unity’s lifecycle quirks mean these operators might not behave as expected, potentially causing runtime issues.  
- **For plain C# objects**: Go wild! These operators make your code safer and more elegant. 🎉  

And remember: if you’re working in a team or using external plugins, avoid patterns that rely on these operators for Unity objects. Not everyone will be aware of the caveats, and bugs might creep in like ninjas. 🤺  


---

### **References 📚**  

1. Microsoft Learn: [C# Operators Overview](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/operators/)  
2. Rider resharper-unity: [Unintended Bypass Of Lifetime](https://github.com/JetBrains/resharper-unity/wiki/Possible-unintended-bypass-of-lifetime-check-of-underlying-Unity-engine-object)  
3. Unity Blog: [Custom == operator, should we keep it?](https://unity.com/blog/engine-platform/custom-operator-should-we-keep-it)  

Got war stories or lessons learned about using these operators in Unity? Share them in the comments—let’s learn and laugh together! 😄  
