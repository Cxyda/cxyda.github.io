---
layout: post
title: Understanding Structs and Classes in C#
tags: [C#,Unity3D]
# lastmod: 2024-11-17
---

When diving into the C# multiverse 🌌, we inevitably face the age-old questions about **where data lives**, **how the garbage collector (GC) behaves**, and **the eternal battle between structs and classes**. 🛠️ In this post, we’ll tackle these concepts with precision, dispel some myths, and arm you with actionable knowledge to level up your .NET skills. ⚡  

---

### **1. Are Large Structs Automatically Moved to the Heap?**  

#### 🧠 Question:  
Some claim that structs larger than 16 bytes get auto-promoted to the heap like VIPs at a concert. 🎤 Is this legit? Where do behemoth structs (like a 1 MB struct 🏋️) reside?  

#### 💡 Answer:  
Nope! Large structs don’t magically teleport to the heap unless **explicitly boxed** 🪄 or placed within a reference type (e.g., a class or array). Structs are value types, and their storage location depends on their context:  

- **Local variables**: Stored on the **stack** 🥞, no matter their size.  
- **Fields of a class**: Stored on the **heap** 🗂️, as part of the class instance.  
- **Boxed structs**: Stored on the **heap**, wrapped in a shiny object wrapper.  

⚠️ Beware, adventurer! Using monstrous structs (e.g., 1 MB) on the stack risks summoning the dreaded `StackOverflowException` 💀, as the stack has limited space (a few MB per thread). To avoid this peril, Microsoft advises keeping structs compact—preferably under **16–32 bytes**—for smooth sailing. 🚀  

---

### **2. How Does the GC Handle Arrays of Classes vs. Structs?**  

#### 🤔 Question:  
When the GC visits an array of classes (`CustomClass[]`) or structs (`CustomStruct[]`), does it handle them differently? Do structs in arrays simply “poof” 💨, or does the GC grind through them one by one?  

#### 🔍 Answer:  
Oh, there’s a key difference in how the GC processes arrays of classes and structs:  

- **Array of Classes (`CustomClass[]`)**:  
  - The array itself is a **reference type**, living large on the heap. 🏠  
  - Each element is a reference (pointer) to a `CustomClass` instance, which is also allocated on the heap.  
  - When the GC runs, it must play detective 🕵️‍♂️, traversing the array and individually releasing each `CustomClass` instance if no other references exist. This can be **slow**—think of it as having to clean 1000 rooms in a hotel. 🏨  

- **Array of Structs (`CustomStruct[]`)**:  
  - The array is still a reference type on the heap, but here’s the twist: the structs are stored **inline** in the array’s memory block. 🧱  
  - When the array is garbage collected, all struct data is wiped out in one fell swoop. 🎯 The GC doesn’t process individual structs, making this approach **leaner and meaner**.  

This structural advantage makes arrays of structs more GC-friendly 🐉, though they can still have trade-offs, like higher copying costs for large structs.  

---

### **3. How Do `readonly` Structs and the `in` Keyword Impact Performance?**  

#### ⚡ Question:  
What wizardry happens when you pass a large `readonly` struct to a method using the `in` keyword? How does this black magic affect memory allocation and performance? 🪄  

#### 🛠️ Answer:  
The **`readonly`** modifier keeps your struct immutable (think of it as the unshakable Jedi of the struct world 🧘‍♂️), and the `in` keyword passes it by reference rather than by value. This combo lets you wield large structs efficiently during method calls without the burden of copying.  

- **Performance Perks**:  
  - Passing structs with `in` eliminates costly copying 🏎️, especially for structs larger than 16 bytes.  
  - The compiler ensures immutability, so your method can’t modify the struct. This is both safe and elegant—like Gandalf shouting, “You shall not mutate!” 🧙‍♂️  

- **Memory Magic**:  
  - The struct stays right where it was born (stack or heap), and the method receives a reference. No extra allocations, no fuss. ✨  

---

### **4. Are Arrays Always Stored on the Heap, Even When Declared Locally?**  

#### 🧐 Question:  
If I declare an array locally in a method, does it still chill on the heap? What about its elements? 🗃️  

#### 🔑 Answer:  
Yes! Arrays in C# are **always** stored on the heap, regardless of where you declare them. 🏰  

- The array reference (a pointer) lives on the stack if declared locally, but the array object itself is firmly planted on the heap. 🌱  
- For arrays of structs, the struct data is embedded inline within the array block on the heap. For arrays of classes, the array stores references to objects, which are also heap-allocated.  

---

### **Conclusion: Leveling Up Your Struct-and-Class Kung Fu 🥋**  

Understanding the subtleties of structs, classes, and GC is essential for mastering C# development. Here’s your TL;DR spellbook 🧙‍♀️:  

1. Large structs don’t magically migrate to the heap but can cause stack troubles if oversized. Keep them small for peak performance. 🏋️‍♀️  
2. Arrays of structs are **GC-friendly** because the GC doesn’t process each struct individually. 🗑️ Arrays of classes, on the other hand, involve more overhead.  
3. Use **`readonly` structs + `in`** to pass large structs efficiently while preserving immutability. 🏹  
4. Arrays always hang out on the heap, no matter where they’re declared. 🏠  

By embracing these principles, you’ll wield the power of C# with the precision of a legendary developer. ⚔️ Your applications will thank you—with fewer bugs and smoother performance! 🚀  

---

### **References 📚**  

1. Microsoft Learn: [C# Structs](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/builtin-types/struct)  
2. .NET Team Blog: [Choosing Between Classes and Structs](https://devblogs.microsoft.com/dotnet/)  
3. Microsoft Learn: [Garbage Collection in .NET](https://learn.microsoft.com/en-us/dotnet/standard/garbage-collection/)  
4. Eric Lippert’s Blog: [Value Types and Reference Types](https://ericlippert.com/)  
5. Microsoft Learn: [The `in` Parameter Modifier](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/keywords/in-parameter-modifier)  
6. Performance Tips for Large Structs: [Benchmarking Structs and Classes](https://learn.microsoft.com/en-us/dotnet/performance/)  
7. .NET Memory Management Overview: [Heap vs. Stack](https://learn.microsoft.com/en-us/dotnet/standard/garbage-collection/fundamentals)  
8. Stephen Toub’s Blog: [Understanding Arrays in .NET](https://devblogs.microsoft.com/dotnet/)  

Got thoughts, questions, or war stories about structs and classes? Drop them in the comments! Let’s geek out together. 🤓