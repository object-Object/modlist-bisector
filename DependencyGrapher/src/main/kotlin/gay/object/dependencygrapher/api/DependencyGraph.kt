package gay.`object`.dependencygrapher.api

import kotlinx.serialization.Serializable
import java.nio.file.Path

@Serializable
data class DependencyGraph(
    val dependencies: MutableMap<String, MutableSet<String>>,
    val jars: MutableMap<String, MutableSet<String>>,
) {
    fun addDependencies(modid: String, dependencies: List<String>) {
        if (modid !in this.dependencies) {
            this.dependencies[modid] = mutableSetOf()
        }
        this.dependencies[modid]!!.addAll(dependencies)
    }

    companion object {
        fun empty() = DependencyGraph(mutableMapOf(), mutableMapOf())
    }
}
