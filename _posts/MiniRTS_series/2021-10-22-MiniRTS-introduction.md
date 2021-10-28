---
layout: post
title:  MiniRTS - 01 Introduction
categories: [C#,Unity3D,MiniRTS]
---

In this tutorial series I want to create a mini RealTimeStrategy (RTS) game. The project will include all main features of a common RTS. I will also add multiplayer support to this project. The network architecture will be a [lockstep simulation](https://en.wikipedia.org/wiki/Lockstep_protocol), which is quite common for games in the RTS genre.

I'm going to focus on a good architecture which should allow you to learn from it and extend it to a big project without suffering from a fast but hacky implementation. This of course comes with a drawback. Some implementations might look cumbersome at first or even like overkill for such a small project, but the goal of this series is not to get basic systems working but to create a solid foundation for any RTS project. I assume you have at least basic knowledge about Unity, so this series will not explain you how to do basic thing in Unity. If you are stuck on some steps, I'm sure google can help you out. Otherwise, feel free to drop me some lines.

There won't be any fancy graphics, so don't be disappointed that it looks bad at the end. I'll also keep in mind that you might want to replace my coder artwork with your own to start the next big RTS hit.

This project will use *Extenject* (formerly know as [Zenject](https://github.com/modesttree/Zenject)) for [Dependency Injection](https://en.wikipedia.org/wiki/Dependency_injection).


#### Content of this series (might change on the go)

1. Basic project setup
1. Selection and Input handling
1. Building Placement and Factories
1. UI and Asset Management
1. Units and Resource Gathering
1. Camera Controls
1. Battle
1. Fog od War
1. Lockstep Simulation
1. Networking
1. TechTrees

#### Technology used
- [Unity3D 2021.1.15f1](https://unity3d.com/de/get-unity/download)
- [Extenject framework](https://assetstore.unity.com/packages/tools/utilities/extenject-dependency-injection-ioc-157735)
- [Photon Engine](https://www.photonengine.com/pun)

**Let's have a very good time together and let's get started!**

##### | [Selection and input handling >]({% post_url 2021-10-23-MiniRTS-ProjectSetup %})

2021-10-23-MiniRTS-ProectSetup